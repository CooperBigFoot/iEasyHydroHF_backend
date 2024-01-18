import xml.etree.ElementTree as ET

from dateutil.parser import parse

from sapphire_backend.metrics.models import HydrologicalMetric
from sapphire_backend.stations.models import HydrologicalStation

MAP_XML_VAR_TO_MODEL_VAR = {
    "LW": (HydrologicalMetric.MetricName.WATER_LEVEL_DAILY, HydrologicalMetric.MetricUnit.WATER_LEVEL),
    "TW": (HydrologicalMetric.MetricName.WATER_TEMPERATURE, HydrologicalMetric.MetricUnit.TEMPERATURE),
    "TA": (HydrologicalMetric.MetricName.AIR_TEMPERATURE, HydrologicalMetric.MetricUnit.TEMPERATURE),
    # "LB": None, # LB Battery voltage [V]
    # "SELEM": None, # Status of the technological element
    # "DRS": None, # Open door (0 - closed 1 - open)
    # "CHCU": None, # Power elememnt current [mA]
    # "TELEM": None # The temperature of the technological element [° C]
}


def is_var_name_supported(var_name):
    return MAP_XML_VAR_TO_MODEL_VAR.get(var_name, False)


def save_record(timestamp, station_id, var_name, sensor_type, avg_value, min_value, max_value):
    datetime_object = parse(timestamp)
    hydro_station = HydrologicalStation.objects.get(station_code=station_id)
    metric_name, metric_unit = MAP_XML_VAR_TO_MODEL_VAR[var_name]

    new_hydro_metric = HydrologicalMetric(
        timestamp=datetime_object,
        min_value=min_value,
        avg_value=avg_value,
        max_value=max_value,
        unit=metric_unit,
        value_type=HydrologicalMetric.MeasurementType.AUTOMATIC,
        metric_name=metric_name,
        station=hydro_station,
        sensor_identifier="",
        sensor_type=sensor_type,
    )
    new_hydro_metric.save()


def parse_xml_file(file_path):
    tree = ET.parse(file_path)
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
                for value in parameter:
                    if value.attrib["PROC"] == "AVE":
                        avg_value = float(value.text)
                    elif value.attrib["PROC"] == "MIN":
                        min_value = float(value.text)
                    elif value.attrib["PROC"] == "MAX":
                        max_value = float(value.text)
                if is_var_name_supported(var_name):
                    save_record(timestamp, station_id, var_name, sensor_type, avg_value, min_value, max_value)
