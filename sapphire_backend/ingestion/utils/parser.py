import datetime
import logging
import os
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from types import NoneType
from typing import TypedDict

from dateutil.parser import parse

from sapphire_backend.metrics.models import HydrologicalMetric
from sapphire_backend.stations.models import HydrologicalStation


class MetricRecord(TypedDict):
    timestamp: datetime.datetime
    station: HydrologicalStation
    sensor_type: str
    sensor_identifier: str
    avg_value: float
    min_value: float
    max_value: float
    metric_name: str
    value_type: HydrologicalMetric.MeasurementType
    unit: str


class BaseParser(ABC):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._input_records = []
        self._output_metric_objects = []
        self._cnt_skipped_records = 0

    @property
    def file_name(self):
        dir, file_name = os.path.split(self.file_path)
        return file_name

    @property
    def input_records(self):
        return self._input_records

    @property
    def output_metric_objects(self) -> [HydrologicalMetric]:
        return self._output_metric_objects

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

    @abstractmethod
    def run(self):
        """
        Main parsing method, must be implemented by subclasses
        """

    def save(self):
        """
        Save all the created metric objects
        """
        for metric_object in self.output_metric_objects:
            metric_object.save()


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

    def __init__(self, file_path: str):
        super().__init__(file_path)
        self.map_xml_var_to_model_var = {
            "LW": (HydrologicalMetric.MetricName.WATER_LEVEL_DAILY, HydrologicalMetric.MetricUnit.WATER_LEVEL),
            "TW": (HydrologicalMetric.MetricName.WATER_TEMPERATURE, HydrologicalMetric.MetricUnit.TEMPERATURE),
            "TA": (HydrologicalMetric.MetricName.AIR_TEMPERATURE, HydrologicalMetric.MetricUnit.TEMPERATURE),
        }
        self.log_unsupported_variables = set()
        self.log_unknown_stations = set()

    def is_var_name_supported(self, var_name: str) -> bool:
        return var_name in self.map_xml_var_to_model_var

    def transform_record(self, record_raw: InputRecord) -> MetricRecord | NoneType:
        datetime_object = parse(record_raw["timestamp"])
        # in case of a 6-digit station id, take only the first five digits
        station_id_5digit = record_raw["station_id"][:5]
        try:
            hydro_station_obj = HydrologicalStation.objects.get(station_code=station_id_5digit)
        except HydrologicalStation.DoesNotExist:
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
            value_type=HydrologicalMetric.MeasurementType.AUTOMATIC,
            unit=metric_unit,
        )

        return record_transformed

    def transform(self):
        for record_serialized in self.input_records:
            record_transformed = self.transform_record(record_serialized)
            if record_transformed is not None:
                new_hydro_metric = self.create_metric_object(record_transformed)
                self.output_metric_objects.append(new_hydro_metric)

    def extract(self):
        tree = ET.parse(self.file_path)
        root = tree.getroot()
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
        self.extract()
        self.transform()
        self.save()
        self.post_run()
        logging.info(f"Done parsing {self.file_name}")

    def post_run(self):
        """
        Logging processed and skipped records number.
        """
        logging.info(f"Imported {self.count_parsed_records} records")
        logging.error(f"Unknown stations: {self.log_unknown_stations}")
        logging.info(f"Unsupported variables: {self.log_unsupported_variables}")
        logging.info(f"Skipped {self.count_skipped_records} records")
