import math
from typing import Optional

from sapphire_backend.estimations.utils import get_discharge_model_from_timestamp
from sapphire_backend.metrics.choices import (
    HydrologicalMeasurementType,
    HydrologicalMetricName, MetricUnit,
)
from sapphire_backend.metrics.models import HydrologicalMetric
from sapphire_backend.stations.models import HydrologicalStation
from sapphire_backend.telegrams.schema import TimeData
from sapphire_backend.utils.datetime_helper import SmartDatetime


def save_reported_discharge(measurements: dict, hydro_station: HydrologicalStation):
    for input in measurements:
        timestamp = SmartDatetime(input['date'], hydro_station, local=True).utc
        water_level_decadal_metric = HydrologicalMetric(
            timestamp=timestamp,
            min_value=None,
            avg_value=input["water_level"],
            max_value=None,
            unit=MetricUnit.WATER_LEVEL,
            value_type=HydrologicalMeasurementType.MANUAL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DECADAL,
            station=hydro_station,
            sensor_identifier="",
            sensor_type="",
        )
        water_level_decadal_metric.save()

        discharge_metric = HydrologicalMetric(
            timestamp=timestamp,
            min_value=None,
            avg_value=input["discharge"],
            max_value=None,
            unit=MetricUnit.WATER_DISCHARGE,
            value_type=HydrologicalMeasurementType.MANUAL,
            metric_name=HydrologicalMetricName.WATER_DISCHARGE_DAILY,
            station=hydro_station,
            sensor_identifier="",
            sensor_type="",
        )
        discharge_metric.save()

        cross_section_area_metric = HydrologicalMetric(
            timestamp=timestamp,
            min_value=None,
            avg_value=input["cross_section_area"],
            max_value=None,
            unit=MetricUnit.AREA,
            value_type=HydrologicalMeasurementType.MANUAL,
            metric_name=HydrologicalMetricName.RIVER_CROSS_SECTION_AREA,
            station=hydro_station,
            sensor_identifier="",
            sensor_type="",
        )
        cross_section_area_metric.save()

        maximum_depth_metric = HydrologicalMetric(
            timestamp=timestamp,
            min_value=None,
            avg_value=input["maximum_depth"],
            max_value=None,
            unit=MetricUnit.WATER_LEVEL,
            value_type=HydrologicalMeasurementType.MANUAL,
            metric_name=HydrologicalMetricName.MAXIMUM_DEPTH,
            station=hydro_station,
            sensor_identifier="",
            sensor_type="",
        )
        maximum_depth_metric.save()


def build_data_processing_structure(data_list: list):
    """
    Build dict structure based on station_codes, dates which are affected:
    E.g.
    result_struct =
    {"12345" : {
        "2024-02-02": {},
        "2024-02-03": {},
        ...
    },
    "12346": {
        "2024-02-05": {},
        "2024-02-06": {},
        ...
    },
    ...
    }
    :param data_list:
    :return:
    """
    result = {}
    for parsed in data_list:
        station_code = parsed["station_code"]
        if result.get(station_code) is None:
            result[station_code] = {}

        telegram_day_date = parsed["telegram_day_date"]
        previous_day_date = parsed["previous_day_date"]

        result[station_code][telegram_day_date] = result[station_code][previous_day_date] = {
            "morning": {},
            "evening": {},
            "average": {},
        }
    return result


def fill_with_old_metrics(init_struct: dict, organization_uuid: str) -> dict:
    """
    Given the station codes and dates, fill all the metrics _old and _new with the same values as if there will be no
    changes to the _old data.
    """
    # result = init_struct
    result = {}
    for station_code, dates in init_struct.items():
        result[station_code] = {}
        hydro_station = HydrologicalStation.objects.filter(
            station_code=station_code, station_type=HydrologicalStation.StationType.MANUAL,
            site__organization_id=organization_uuid
        ).first()

        for date, metrics in dates.items():
            result[station_code][date] = {}
            smart_date = SmartDatetime(date, hydro_station, local=True)

            # water levels
            water_level_morning_old = getattr(HydrologicalMetric(timestamp=smart_date.morning_utc,
                                                                 metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
                                                                 station=hydro_station,
                                                                 value_type=HydrologicalMeasurementType.MANUAL
                                                                 ).select_first(), 'avg_value', None)
            result[station_code][date]["morning"] = TimeData(water_level_new=None, water_level_old=None,
                                                             discharge_new=None, discharge_old=None)
            result[station_code][date]["morning"].water_level_old = custom_ceil(water_level_morning_old)
            result[station_code][date]["morning"].water_level_new = custom_ceil(water_level_morning_old)

            water_level_evening_old = getattr(HydrologicalMetric(timestamp=smart_date.evening_utc,
                                                                 metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
                                                                 station=hydro_station,
                                                                 value_type=HydrologicalMeasurementType.MANUAL
                                                                 ).select_first(), 'avg_value', None)

            result[station_code][date]["evening"] = TimeData(water_level_new=None, water_level_old=None,
                                                             discharge_new=None, discharge_old=None)
            result[station_code][date]["evening"].water_level_old = custom_ceil(water_level_evening_old)
            result[station_code][date]["evening"].water_level_new = custom_ceil(water_level_evening_old)

            water_level_average_old = getattr(HydrologicalMetric(timestamp=smart_date.midday_utc,
                                                                 metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY_AVERAGE,
                                                                 station=hydro_station,
                                                                 value_type=HydrologicalMeasurementType.ESTIMATED
                                                                 ).select_first(), 'avg_value', None)

            result[station_code][date]["average"] = TimeData(water_level_new=None, water_level_old=None,
                                                             discharge_new=None, discharge_old=None)
            result[station_code][date]["average"].water_level_old = custom_ceil(water_level_average_old)
            result[station_code][date]["average"].water_level_new = custom_ceil(water_level_average_old)

            # discharges
            discharge_morning_old = getattr(HydrologicalMetric(timestamp=smart_date.morning_utc,
                                                               metric_name=HydrologicalMetricName.WATER_DISCHARGE_DAILY,
                                                               station=hydro_station,
                                                               value_type=HydrologicalMeasurementType.ESTIMATED
                                                               ).select_first(), 'avg_value', None)

            result[station_code][date]["morning"].discharge_old = custom_round(discharge_morning_old, 1)
            result[station_code][date]["morning"].discharge_new = custom_round(discharge_morning_old, 1)

            discharge_evening_old = getattr(HydrologicalMetric(timestamp=smart_date.evening_utc,
                                                               metric_name=HydrologicalMetricName.WATER_DISCHARGE_DAILY,
                                                               station=hydro_station,
                                                               value_type=HydrologicalMeasurementType.ESTIMATED
                                                               ).select_first(), 'avg_value', None)

            result[station_code][date]["evening"].discharge_old = custom_round(discharge_evening_old, 1)
            result[station_code][date]["evening"].discharge_new = custom_round(discharge_evening_old, 1)

            discharge_average_old = getattr(HydrologicalMetric(timestamp=smart_date.midday_utc,
                                                               metric_name=HydrologicalMetricName.WATER_DISCHARGE_DAILY_AVERAGE,
                                                               station=hydro_station,
                                                               value_type=HydrologicalMeasurementType.ESTIMATED
                                                               ).select_first(), 'avg_value', None)

            result[station_code][date]["average"].discharge_old = custom_round(discharge_average_old, 1)
            result[station_code][date]["average"].discharge_new = custom_round(discharge_average_old, 1)
    return result


def insert_new_metrics(data_template: dict, data_list: list, organization_uuid: str) -> dict:
    result = data_template
    for parsed in data_list:
        station_code = parsed["station_code"]
        telegram_day_date = parsed["telegram_day_date"]
        hydro_station = HydrologicalStation.objects.filter(
            station_code=station_code, station_type=HydrologicalStation.StationType.MANUAL,
            site__organization_id=organization_uuid
        ).first()
        smart_datetime = SmartDatetime(telegram_day_date, hydro_station, local=True)

        wl_morning_new = parsed["section_one"]["telegram_day_morning_water_level"]

        discharge_model = get_discharge_model_from_timestamp(station=hydro_station,
                                                             timestamp=smart_datetime.morning_utc)
        discharge_morning_new = discharge_model.estimate_discharge(wl_morning_new)

        result[station_code][telegram_day_date]["morning"].water_level_new = custom_ceil(wl_morning_new)
        result[station_code][telegram_day_date]["morning"].discharge_new = custom_round(discharge_morning_new, 1)

        # previous day evening

        previous_day_date = parsed["previous_day_date"]
        wl_previous_evening_new = parsed["section_one"]["previous_day_evening_water_level"]

        discharge_model = get_discharge_model_from_timestamp(station=hydro_station,
                                                             timestamp=smart_datetime.previous_evening_utc)
        discharge_previous_evening_new = discharge_model.estimate_discharge(wl_previous_evening_new)

        result[station_code][previous_day_date]["evening"].water_level_new = custom_ceil(wl_previous_evening_new)
        result[station_code][previous_day_date]["evening"].discharge_new = custom_round(discharge_previous_evening_new,
                                                                                        1)
    return result


def insert_new_averages(data_template: dict, organization_uuid: str) -> dict:
    """
    Calculate average based on morning and evening water_level_new and estimate average discharge accordingly
    :param data_template:
    :param organization_uuid:
    :return:
    """
    result = {}
    for station_code, dates in data_template.items():
        result[station_code] = {}
        hydro_station = HydrologicalStation.objects.filter(
            station_code=station_code, station_type=HydrologicalStation.StationType.MANUAL,
            site__organization_id=organization_uuid
        ).first()

        for date, metrics in dates.items():
            smart_datetime = SmartDatetime(date, hydro_station, local=True)
            result[station_code][date] = data_template[station_code][date]
            wl_morning_new = result[station_code][date]["morning"].water_level_new
            wl_evening_new = result[station_code][date]["evening"].water_level_new

            discharge_average_new = None
            discharge_model = get_discharge_model_from_timestamp(station=hydro_station,
                                                                 timestamp=smart_datetime.midday_utc)
            if None not in [wl_morning_new, wl_evening_new]:
                wl_average_new = (wl_morning_new + wl_evening_new) / 2
                discharge_average_new = discharge_model.estimate_discharge(wl_average_new)
            elif wl_morning_new is None and wl_evening_new is None:
                wl_average_new = None
            else:
                wl_average_new = wl_morning_new or wl_evening_new
                discharge_average_new = discharge_model.estimate_discharge(wl_average_new)

            result[station_code][date]["average"].water_level_new = custom_ceil(wl_average_new)
            result[station_code][date]["average"].discharge_new = custom_round(discharge_average_new, 1)

    return result


def custom_round(value: Optional[float], ndigits: Optional[int] = None) -> Optional[float]:
    """
    Custom round accepts float and None, returns None if so
    """
    if value is None:
        return None
    return round(float(value), ndigits)


def custom_ceil(value: Optional[int]) -> Optional[int]:
    """
    Custom ceil accepts float and None, returns None if so
    """
    if value is None:
        return None
    return math.ceil(value)
