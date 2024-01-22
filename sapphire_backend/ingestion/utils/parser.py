import logging
import xml.etree.ElementTree as ET

from dateutil.parser import parse

from sapphire_backend.metrics.models import HydrologicalMetric
from sapphire_backend.stations.models import HydrologicalStation


class ParserBase:
    def __init__(self, file_path):
        self.file_path = file_path
        self.input_records = []
        self.output_metric_objects = []
        self.cnt_skipped_records = 0

    def get_input_records(self):
        return self.input_records

    def append_output_metric_objects(self, record: []):
        self.output_metric_objects.append(record)

    def increment_skipped(self):
        self.cnt_skipped_records = self.cnt_skipped_records + 1

    def count_parsed_records(self):
        return len(self.get_input_records())

    def count_skipped_records(self):
        return self.cnt_skipped_records

    @staticmethod
    def create_metric_object(record: {}) -> HydrologicalMetric:
        new_hydro_metric = HydrologicalMetric(
            timestamp=record["timestamp"],
            min_value=record["min_value"],
            avg_value=record["avg_value"],
            max_value=record["max_value"],
            unit=record["unit"],
            value_type=HydrologicalMetric.MeasurementType.AUTOMATIC,
            metric_name=record["metric_name"],
            station=record["station"],
            sensor_identifier=record["sensor_identifier"],
            sensor_type=record["sensor_type"],
        )
        return new_hydro_metric

    def input_append(self, timestamp: str, station_id: str, var_name: str, sensor_type: str, sensor_id: str,
                     avg_value: str, min_value: str,
                     max_value: str):
        """
        Serialize input and append the list of input records.
        """
        input_record = {"timestamp": timestamp,
                        "station_id": station_id,
                        "var_name": var_name,
                        "sensor_type": sensor_type,
                        "sensor_id": sensor_id,
                        "avg_value": avg_value,
                        "min_value": min_value,
                        "max_value": max_value,
                        }
        self.input_records.append(input_record)

    def run(self):
        pass

    def post_run(self):
        """
        Logging processed and skipped records number.
        """
        logging.info(f"Processed {self.count_parsed_records()} records")
        logging.info(f"Skipped {self.count_skipped_records()} records")

    def save(self):
        """
        Save all the created metric objects
        """
        for metric_object in self.output_metric_objects:
            metric_object.save()


class XMLParser(ParserBase):
    def __init__(self, file_path: str):
        super(XMLParser, self).__init__(file_path)
        self.map_xml_var_to_model_var = {
            "LW": (HydrologicalMetric.MetricName.WATER_LEVEL_DAILY, HydrologicalMetric.MetricUnit.WATER_LEVEL),
            "TW": (HydrologicalMetric.MetricName.WATER_TEMPERATURE, HydrologicalMetric.MetricUnit.TEMPERATURE),
            "TA": (HydrologicalMetric.MetricName.AIR_TEMPERATURE, HydrologicalMetric.MetricUnit.TEMPERATURE),
            # "LB": None, # LB Battery voltage [V]
            # "SELEM": None, # Status of the technological element
            # "DRS": None, # Open door (0 - closed 1 - open)
            # "CHCU": None, # Power elememnt current [mA]
            # "TELEM": None # The temperature of the technological element [° C]
        }

    def is_var_name_supported(self, var_name: str) -> bool:
        return var_name in self.map_xml_var_to_model_var

    def transform_record(self, record_raw: dict) -> dict:
        datetime_object = parse(record_raw["timestamp"])
        hydro_station_obj = HydrologicalStation.objects.get(station_code=record_raw["station_id"])
        metric_name, metric_unit = self.map_xml_var_to_model_var[record_raw["var_name"]]
        avg_value = record_raw.get("avg_value", None)
        if avg_value is not None:
            avg_value = float(avg_value)
        min_value = record_raw.get("min_value", None)
        if min_value is not None:
            min_value = float(min_value)
        max_value = record_raw.get("max_value", None)
        if max_value is not None:
            max_value = float(max_value)
        record_transformed = {"timestamp": datetime_object,
                              "station": hydro_station_obj,
                              "sensor_type": record_raw.get("sensor_type", None),
                              "sensor_identifier": record_raw.get("sensor_id", None),
                              "avg_value": avg_value,
                              "min_value": min_value,
                              "max_value": max_value,
                              "metric_name": metric_name,
                              "unit": metric_unit,
                              }
        return record_transformed

    def transform(self):
        for record_serialized in self.get_input_records():
            record_transformed = self.transform_record(record_serialized)
            new_hydro_metric = self.create_metric_object(record_transformed)
            self.append_output_metric_objects(new_hydro_metric)

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
                    sensor_type = parameter.attrib.get("SENSTYPE", None)
                    sensor_identifier = parameter.attrib.get("SENSID", None)  # TODO so far no xml files with this
                    if self.is_var_name_supported(var_name):
                        for value in parameter:
                            if value.attrib["PROC"] == "AVE":
                                avg_value = value.text
                            elif value.attrib["PROC"] == "MIN":
                                min_value = value.text
                            elif value.attrib["PROC"] == "MAX":
                                max_value = value.text
                        self.input_append(timestamp, station_id, var_name, sensor_type,
                                          sensor_identifier, avg_value, min_value, max_value)
                    else:
                        self.increment_skipped()
                        logging.info(f"Skipped parsing unsupported {var_name} variable")

    def run(self):
        self.extract()
        self.transform()
        self.save()
        self.post_run()
