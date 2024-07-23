import datetime
import gzip
import logging
import os
import re
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from types import NoneType
from typing import TypedDict

import zoneinfo
from django.utils import timezone

from sapphire_backend.ingestion.models import FileState
from sapphire_backend.ingestion.utils.helper import get_or_create_auto_station_by_code
from sapphire_backend.metrics.choices import HydrologicalMeasurementType, HydrologicalMetricName, MetricUnit
from sapphire_backend.metrics.models import HydrologicalMetric
from sapphire_backend.organizations.models import Organization
from sapphire_backend.stations.models import HydrologicalStation
from sapphire_backend.telegrams.models import TelegramReceived
from sapphire_backend.telegrams.parser import KN15TelegramParser


class MetricRecord(TypedDict):
    timestamp: datetime.datetime
    station: HydrologicalStation
    sensor_type: str
    sensor_identifier: str
    avg_value: float
    min_value: float
    max_value: float
    metric_name: str
    value_type: HydrologicalMeasurementType
    unit: str


class BaseParser(ABC):
    def __init__(self, file_path: str, organization: Organization, filestate: FileState):
        self.file_path = file_path
        self._filestate = filestate
        self._input_records = []
        self._output_metric_objects = []
        self._cnt_skipped_records = 0
        self._organization = organization

    @property
    def file_name(self):
        dir, file_name = os.path.split(self.file_path)
        return file_name

    @abstractmethod
    def run(self):
        """
        Main parsing method, must be implemented by subclasses
        """
        pass

    @abstractmethod
    def save(self):
        """
        Save all the parsed objects
        """
        pass


class XMLParser(BaseParser):
    class InputRecord(TypedDict):
        timestamp: str
        station_id: str
        var_name: str
        sensor_type: str
        sensor_id: str
        avg_value: str
        min_value: str
        max_value: str

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.map_xml_var_to_model_var = {
            "LW": (HydrologicalMetricName.WATER_LEVEL_DAILY, MetricUnit.WATER_LEVEL),
            "TW": (HydrologicalMetricName.WATER_TEMPERATURE, MetricUnit.TEMPERATURE),
            "TA": (HydrologicalMetricName.AIR_TEMPERATURE, MetricUnit.TEMPERATURE),
        }
        self.log_unsupported_variables = set()
        self.log_unknown_stations = set()

    def is_var_name_supported(self, var_name: str) -> bool:
        return var_name in self.map_xml_var_to_model_var

    @property
    def input_records(self):
        return self._input_records

    def increment_skipped(self):
        self._cnt_skipped_records = self._cnt_skipped_records + 1

    @property
    def count_parsed_records(self) -> int:
        return len(self.input_records)

    @property
    def count_skipped_records(self) -> int:
        return self._cnt_skipped_records

    @staticmethod
    def create_metric_object(record: MetricRecord) -> HydrologicalMetric:
        new_hydro_metric = HydrologicalMetric(
            timestamp=record["timestamp"],
            min_value=record["min_value"],
            avg_value=record["avg_value"],
            max_value=record["max_value"],
            unit=record["unit"],
            value_type=record["value_type"],
            metric_name=record["metric_name"],
            station=record["station"],
            sensor_identifier=record["sensor_identifier"],
            sensor_type=record["sensor_type"],
        )
        return new_hydro_metric

    @property
    def output_metric_objects(self) -> [HydrologicalMetric]:
        return self._output_metric_objects

    @staticmethod
    def convert_str_to_datetime(datetime_str: str) -> datetime.datetime:
        """
        Convert timestamp string to datetime UTC object
        """
        dt_object = timezone.datetime.strptime(datetime_str, "%d-%m-%YT%H:%M:%SZ")
        dt_object_utc = timezone.make_aware(dt_object, zoneinfo.ZoneInfo("UTC"))
        return dt_object_utc

    def save(self):
        for metric_object in self.output_metric_objects:
            metric_object.save()

    def transform_record(self, record_raw: InputRecord) -> MetricRecord | NoneType:
        datetime_object = self.convert_str_to_datetime(record_raw["timestamp"])
        # in case of a 6-digit station id, take only the first five digits
        station_id_5digit = record_raw["station_id"][:5]

        hydro_station_obj = get_or_create_auto_station_by_code(
            station_code=station_id_5digit, organization=self._organization
        )
        if hydro_station_obj is None:
            self.log_unknown_stations.add(station_id_5digit)
            return

        metric_name, metric_unit = self.map_xml_var_to_model_var[record_raw["var_name"]]
        try:
            avg_value = record_raw.get("avg_value", None)
            if avg_value is not None:
                avg_value = float(avg_value)
            min_value = record_raw.get("min_value", None)
            if min_value is not None:
                min_value = float(min_value)
            max_value = record_raw.get("max_value", None)
            if max_value is not None:
                max_value = float(max_value)
        except ValueError:
            logging.error(
                f"Value error for {record_raw['timestamp']} avg {record_raw['avg_value']} min {record_raw['min_value']} max {record_raw['max_value']}. Skipping..."
            )
            return

        record_transformed = MetricRecord(
            timestamp=datetime_object,
            station=hydro_station_obj,
            sensor_type=record_raw.get("sensor_type", ""),
            sensor_identifier=record_raw.get("sensor_id", ""),
            avg_value=avg_value,
            min_value=min_value,
            max_value=max_value,
            metric_name=metric_name,
            value_type=HydrologicalMeasurementType.AUTOMATIC,
            unit=metric_unit,
        )

        return record_transformed

    def transform(self):
        for record_serialized in self.input_records:
            record_transformed = self.transform_record(record_serialized)
            if record_transformed is not None:
                new_hydro_metric = self.create_metric_object(record_transformed)
                self.output_metric_objects.append(new_hydro_metric)

    def _read_xml_data(self) -> str:
        """
        Read a file either raw or gzipped and return data as string
        """
        filename, ext = os.path.splitext(self.file_path)
        if ext == ".gz":
            with gzip.open(self.file_path, "rb") as f_gzipped:
                xml_data = f_gzipped.read().decode("utf-8")
        else:
            with open(self.file_path) as f_raw:
                xml_data = f_raw.read()
        return xml_data

    def extract(self, xml_data: str):
        root = ET.fromstring(xml_data)
        for report in root:
            timestamp = report.attrib["TIME"]
            for child in report:
                if child.tag == "station":
                    station_id = child.attrib["ID"]
                elif child.tag == "parameter":
                    parameter = child
                    var_name = parameter.attrib["VAR"]
                    sensor_type = parameter.attrib.get("SENSTYPE", "")
                    sensor_identifier = parameter.attrib.get("SENSID", "")  # TODO so far no xml files with this
                    if self.is_var_name_supported(var_name):
                        for value in parameter:
                            if value.attrib["PROC"] == "AVE":
                                avg_value = value.text
                            elif value.attrib["PROC"] == "MIN":
                                min_value = value.text
                            elif value.attrib["PROC"] == "MAX":
                                max_value = value.text

                        new_record = self.InputRecord(
                            timestamp=timestamp,
                            station_id=station_id,
                            var_name=var_name,
                            sensor_type=sensor_type,
                            sensor_identifier=sensor_identifier,
                            avg_value=avg_value,
                            min_value=min_value,
                            max_value=max_value,
                        )
                        self.input_records.append(new_record)
                    else:
                        self.increment_skipped()
                        self.log_unsupported_variables.add(var_name)

    def run(self):
        logging.info(f"Begin parsing {self.file_name}")
        xml_data = self._read_xml_data()
        self.extract(xml_data)
        self.transform()
        self.save()
        self.post_run()
        logging.info(f"Done parsing {self.file_name}")

    def post_run(self):
        """
        Logging processed and skipped records number.
        """
        logging.info(f"Imported {self.count_parsed_records} records")
        if len(self.log_unknown_stations) > 0:
            logging.error(f"Unknown stations: {self.log_unknown_stations}")
        if len(self.log_unsupported_variables) > 0:
            logging.info(f"Unsupported variables: {self.log_unsupported_variables}")
        logging.info(f"Skipped {self.count_skipped_records} records")


class ZKSParser(BaseParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log_unsupported_variables = set()
        self.log_unknown_stations = set()
        self._telegrams_list = []

    def _read_txt_data(self) -> str:
        """
        Read a file either raw or gzipped and return data as string
        """
        filename, ext = os.path.splitext(self.file_path)
        if ext == ".gz":
            with gzip.open(self.file_path, "rt") as f_gzipped:
                txt_data = f_gzipped.read()
        else:
            with open(self.file_path) as f_raw:
                txt_data = f_raw.read()
        return txt_data

    @property
    def telegrams_list(self):
        return self._telegrams_list

    def _extract_telegram_strings(self, txt_data):
        # Replace all newlines with a single whitespace
        content = txt_data.replace("\n", " ")

        # Remove the EOF character (0x03)
        content = content.replace("\x03", "")

        # Reduce multiple whitespaces to a single whitespace
        content = re.sub(r"\s+", " ", content)

        content = content.rsplit("HHZZ ")[-1]  # accept only data after "HHZZ "

        # Remove whitespace on edges
        content = content.strip()

        # Split the content into parts by '='
        telegrams_list_raw = content.split("=")
        telegrams_stripped_with_equal = [f"{x.strip()}=" for x in telegrams_list_raw if x != ""]
        self._telegrams_list = telegrams_stripped_with_equal

    def save(self):
        for telegram in self.telegrams_list:
            decoded = ""
            errors = ""
            valid = True
            station_code = ""
            try:
                parser = KN15TelegramParser(
                    telegram, organization_uuid=self._organization.uuid, store_parsed_telegram=False
                )
                decoded = parser.parse()
                station_code = decoded["section_zero"]["station_code"]
            except Exception as e:
                valid = False
                errors = repr(e)
            new_telegram_pending_obj = TelegramReceived(
                telegram=telegram,
                station_code=station_code,
                filestate=self._filestate,
                decoded_values=decoded,
                errors=errors,
                valid=valid,
                organization=self._organization,
            )
            new_telegram_pending_obj.save()

    def run(self):
        logging.info(f"Begin parsing {self.file_name}")
        txt_data = self._read_txt_data()
        self._extract_telegram_strings(txt_data)
        self.save()
        self.post_run()
        logging.info(f"Done parsing {self.file_name}")

    def post_run(self):
        """
        Logging imported telegrams stats
        """
        logging.info(f"Imported {len(self.telegrams_list)} telegrams")
