import logging
import math
from datetime import timedelta

from sapphire_backend.estimations.utils import get_discharge_model_from_timestamp
from sapphire_backend.metrics.choices import (
    HydrologicalMeasurementType,
    HydrologicalMetricName,
    MeteorologicalMeasurementType,
    MeteorologicalMetricName,
    MetricUnit,
)
from sapphire_backend.metrics.models import HydrologicalMetric, MeteorologicalMetric
from sapphire_backend.metrics.timeseries.query import TimeseriesQueryManager
from sapphire_backend.stations.models import HydrologicalStation, MeteorologicalStation
from sapphire_backend.telegrams.exceptions import TelegramParserException
from sapphire_backend.telegrams.parser import KN15TelegramParser
from sapphire_backend.telegrams.schema import NewOldMetrics, TelegramBulkWithDatesInputSchema
from sapphire_backend.utils.datetime_helper import SmartDatetime


def custom_round(value: float | None, ndigits: int | None = None) -> float | None:
    """
    Custom round accepts float and None, returns None if so
    """
    if value is None:
        return None
    return round(float(value), ndigits)


def custom_ceil(value: int | None) -> int | None:
    """
    Custom ceil accepts float and None, returns None if so
    """
    if value is None:
        return None
    return math.ceil(value)


def get_parsed_telegrams_data(
    encoded_telegrams_dates: TelegramBulkWithDatesInputSchema, organization_uuid: str, save_telegrams: bool = True
) -> dict:
    """
    Parse telegrams and add more context
    :return:
    """
    hydro_station_codes = set()
    meteo_station_codes = set()
    parsed_data = {"stations": {}, "discharge_codes": [], "meteo_codes": [], "errors": []}

    for idx, telegram_input in enumerate(encoded_telegrams_dates.telegrams):
        telegram = telegram_input.raw
        override_date = telegram_input.override_date
        parser = KN15TelegramParser(
            telegram, organization_uuid=organization_uuid, store_parsed_telegram=save_telegrams
        )
        try:
            decoded = parser.parse()

            telegram_day_smart = SmartDatetime(decoded["section_zero"]["date"], parser.hydro_station, local=True)
            if override_date is not None:
                telegram_day_smart = SmartDatetime(override_date, parser.hydro_station, local=True)

            decoded["telegram_day_smart"] = telegram_day_smart
            station_code = decoded["section_zero"]["station_code"]
            if parsed_data["stations"].get(station_code) is None:
                parsed_data["stations"][station_code] = {
                    "telegrams": [decoded],
                    "hydro_station_obj": parser.hydro_station,
                    "meteo_station_obj": parser.meteo_station,
                }
            else:
                parsed_data["stations"][station_code]["telegrams"].append(decoded)

            if decoded.get("section_one") is not None:
                hydro_station_codes.add((station_code, str(parser.hydro_station.uuid)))

            if decoded.get("section_eight") is not None:
                meteo_station_codes.add((station_code, str(parser.meteo_station.uuid)))

        except TelegramParserException as e:
            parsed_data["errors"].append({"index": idx, "telegram": telegram, "error": str(e)})
            logging.exception(e)

    parsed_data["hydro_station_codes"] = list(hydro_station_codes)
    parsed_data["meteo_station_codes"] = list(meteo_station_codes)
    return parsed_data


def save_section_one_metrics(telegram_day_smart: SmartDatetime, section_one: dict, hydro_station: HydrologicalStation):
    yesterday_evening_wl_metric = HydrologicalMetric(
        timestamp=telegram_day_smart.previous_evening_utc,
        min_value=None,
        avg_value=section_one["water_level_20h_period"],
        max_value=None,
        unit=MetricUnit.WATER_LEVEL,
        value_type=HydrologicalMeasurementType.MANUAL,
        metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
        station=hydro_station,
        sensor_identifier="",
        sensor_type="",
    )
    yesterday_evening_wl_metric.save(refresh_view=True)

    morning_wl_metric = HydrologicalMetric(
        timestamp=telegram_day_smart.morning_utc,
        min_value=None,
        avg_value=section_one["morning_water_level"],
        max_value=None,
        unit=MetricUnit.WATER_LEVEL,
        value_type=HydrologicalMeasurementType.MANUAL,
        metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
        station=hydro_station,
        sensor_identifier="",
        sensor_type="",
    )
    morning_wl_metric.save(refresh_view=True)

    if section_one.get("air_temperature", False):
        air_temp_metric = HydrologicalMetric(
            timestamp=telegram_day_smart.morning_utc,
            min_value=None,
            avg_value=section_one["air_temperature"],
            max_value=None,
            unit=MetricUnit.TEMPERATURE,
            value_type=HydrologicalMeasurementType.MANUAL,
            metric_name=HydrologicalMetricName.AIR_TEMPERATURE,
            station=hydro_station,
            sensor_identifier="",
            sensor_type="",
        )
        air_temp_metric.save(refresh_view=False)

    if section_one.get("water_temperature", False):
        water_temp_metric = HydrologicalMetric(
            timestamp=telegram_day_smart.morning_utc,
            min_value=None,
            avg_value=section_one["water_temperature"],
            max_value=None,
            unit=MetricUnit.TEMPERATURE,
            value_type=HydrologicalMeasurementType.MANUAL,
            metric_name=HydrologicalMetricName.WATER_TEMPERATURE,
            station=hydro_station,
            sensor_identifier="",
            sensor_type="",
        )
        water_temp_metric.save(refresh_view=False)

    if section_one.get("ice_phenomena"):
        for idx, record in enumerate(section_one["ice_phenomena"]):
            ice_phenomena_metric = HydrologicalMetric(
                timestamp=telegram_day_smart.morning_utc + timedelta(milliseconds=idx),
                min_value=None,
                avg_value=record["intensity"] if record["intensity"] else -1,
                max_value=None,
                unit=MetricUnit.ICE_PHENOMENA_OBSERVATION,
                value_type=HydrologicalMeasurementType.MANUAL,
                metric_name=HydrologicalMetricName.ICE_PHENOMENA_OBSERVATION,
                station=hydro_station,
                sensor_identifier="",
                sensor_type="",
                value_code=record["code"],
            )
            ice_phenomena_metric.save(refresh_view=False)

    if section_one.get("daily_precipitation"):
        daily_precipitation_metric = HydrologicalMetric(
            timestamp=telegram_day_smart.previous_evening_utc,
            min_value=None,
            avg_value=section_one["daily_precipitation"]["precipitation"],
            max_value=None,
            unit=MetricUnit.PRECIPITATION,
            value_type=HydrologicalMeasurementType.MANUAL,
            metric_name=HydrologicalMetricName.DAILY_PRECIPITATION,
            station=hydro_station,
            sensor_identifier="",
            sensor_type="",
            value_code=section_one["daily_precipitation"]["duration_code"],
        )
        daily_precipitation_metric.save(refresh_view=False)


def save_reported_discharge(measurements: dict, hydro_station: HydrologicalStation):
    for input in measurements:
        timestamp = SmartDatetime(input["date"], hydro_station, local=True).utc
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
        if input["maximum_depth"] is not None:
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


def save_section_eight_metrics(meteo_data: dict, meteo_station: MeteorologicalStation) -> None:
    timestamp = meteo_data["timestamp"]
    decade = meteo_data["decade"]
    precipitation_metric = MeteorologicalMetric(
        timestamp=timestamp,
        value=meteo_data["precipitation"],
        value_type=MeteorologicalMeasurementType.MANUAL,
        metric_name=MeteorologicalMetricName.PRECIPITATION_DECADE_AVERAGE
        if decade != 4
        else MeteorologicalMetricName.PRECIPITATION_MONTH_AVERAGE,
        unit=MetricUnit.PRECIPITATION,
        station=meteo_station,
    )
    precipitation_metric.save()

    temperature_metric = MeteorologicalMetric(
        timestamp=timestamp,
        value=meteo_data["temperature"],
        value_type=MeteorologicalMeasurementType.MANUAL,
        metric_name=MeteorologicalMetricName.AIR_TEMPERATURE_DECADE_AVERAGE
        if decade != 4
        else MeteorologicalMetricName.AIR_TEMPERATURE_MONTH_AVERAGE,
        unit=MetricUnit.TEMPERATURE,
        station=meteo_station,
    )
    temperature_metric.save()


def fill_template_with_old_metrics(init_struct: dict, parsed_data: dict) -> dict:
    """
    Given the station codes and dates, fill all the metrics _old and _new with the same values as if there will be no
    changes to the _old data.
    """
    result = {}
    for station_code, dates in init_struct.items():
        result[station_code] = {}
        hydro_station = parsed_data["stations"][station_code]["hydro_station_obj"]

        for date in dates:
            result[station_code][date] = {}
            smart_date = SmartDatetime(date, hydro_station, local=True)

            # water levels
            water_level_morning_old = getattr(
                HydrologicalMetric(
                    timestamp=smart_date.morning_utc,
                    metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
                    station=hydro_station,
                    value_type=HydrologicalMeasurementType.MANUAL,
                ).select_first(),
                "avg_value",
                None,
            )
            result[station_code][date]["morning"] = NewOldMetrics(
                water_level_new=None, water_level_old=None, discharge_new=None, discharge_old=None
            )
            result[station_code][date]["morning"].water_level_old = custom_ceil(water_level_morning_old)
            result[station_code][date]["morning"].water_level_new = custom_ceil(water_level_morning_old)

            water_level_evening_old = getattr(
                HydrologicalMetric(
                    timestamp=smart_date.evening_utc,
                    metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
                    station=hydro_station,
                    value_type=HydrologicalMeasurementType.MANUAL,
                ).select_first(),
                "avg_value",
                None,
            )

            result[station_code][date]["evening"] = NewOldMetrics(
                water_level_new=None, water_level_old=None, discharge_new=None, discharge_old=None
            )
            result[station_code][date]["evening"].water_level_old = custom_ceil(water_level_evening_old)
            result[station_code][date]["evening"].water_level_new = custom_ceil(water_level_evening_old)

            water_level_average_old = getattr(
                HydrologicalMetric(
                    timestamp=smart_date.midday_utc,
                    metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY_AVERAGE,
                    station=hydro_station,
                    value_type=HydrologicalMeasurementType.ESTIMATED,
                ).select_first(),
                "avg_value",
                None,
            )

            result[station_code][date]["average"] = NewOldMetrics(
                water_level_new=None, water_level_old=None, discharge_new=None, discharge_old=None
            )
            result[station_code][date]["average"].water_level_old = custom_ceil(water_level_average_old)
            result[station_code][date]["average"].water_level_new = custom_ceil(water_level_average_old)

            # discharges
            discharge_morning_old = getattr(
                HydrologicalMetric(
                    timestamp=smart_date.morning_utc,
                    metric_name=HydrologicalMetricName.WATER_DISCHARGE_DAILY,
                    station=hydro_station,
                    value_type=HydrologicalMeasurementType.ESTIMATED,
                ).select_first(),
                "avg_value",
                None,
            )

            result[station_code][date]["morning"].discharge_old = custom_round(discharge_morning_old, 1)
            result[station_code][date]["morning"].discharge_new = custom_round(discharge_morning_old, 1)

            discharge_evening_old = getattr(
                HydrologicalMetric(
                    timestamp=smart_date.evening_utc,
                    metric_name=HydrologicalMetricName.WATER_DISCHARGE_DAILY,
                    station=hydro_station,
                    value_type=HydrologicalMeasurementType.ESTIMATED,
                ).select_first(),
                "avg_value",
                None,
            )

            result[station_code][date]["evening"].discharge_old = custom_round(discharge_evening_old, 1)
            result[station_code][date]["evening"].discharge_new = custom_round(discharge_evening_old, 1)

            discharge_average_old = getattr(
                HydrologicalMetric(
                    timestamp=smart_date.midday_utc,
                    metric_name=HydrologicalMetricName.WATER_DISCHARGE_DAILY_AVERAGE,
                    station=hydro_station,
                    value_type=HydrologicalMeasurementType.ESTIMATED,
                ).select_first(),
                "avg_value",
                None,
            )

            result[station_code][date]["average"].discharge_old = custom_round(discharge_average_old, 1)
            result[station_code][date]["average"].discharge_new = custom_round(discharge_average_old, 1)
    return result


def insert_template_with_new_metrics(data_template: dict, parsed_data: dict) -> dict:
    result = data_template
    for station_code, station_data in parsed_data["stations"].items():
        hydro_station = station_data["hydro_station_obj"]
        for telegram_data in station_data["telegrams"]:
            smart_datetime = telegram_data["telegram_day_smart"]
            telegram_day_date = smart_datetime.local.date().isoformat()
            previous_day_date = smart_datetime.previous_local.date().isoformat()

            wl_morning_new = telegram_data["section_one"]["morning_water_level"]

            discharge_model_morning = get_discharge_model_from_timestamp(
                station=hydro_station, timestamp=smart_datetime.morning_utc
            )
            discharge_morning_new = discharge_model_morning.estimate_discharge(wl_morning_new)

            result[station_code][telegram_day_date]["morning"].water_level_new = custom_ceil(wl_morning_new)
            result[station_code][telegram_day_date]["morning"].discharge_new = custom_round(discharge_morning_new, 1)

            # previous day evening
            wl_previous_evening_new = telegram_data["section_one"]["water_level_20h_period"]

            discharge_model_previous_evening = get_discharge_model_from_timestamp(
                station=hydro_station, timestamp=smart_datetime.previous_evening_utc
            )
            discharge_previous_evening_new = discharge_model_previous_evening.estimate_discharge(
                wl_previous_evening_new
            )

            result[station_code][previous_day_date]["evening"].water_level_new = custom_ceil(wl_previous_evening_new)
            result[station_code][previous_day_date]["evening"].discharge_new = custom_round(
                discharge_previous_evening_new, 1
            )
    return result


def insert_new_averages(data_template: dict, parsed_data: dict) -> dict:
    """
    Calculate average based on morning and evening water_level_new and estimate average discharge accordingly
    :param data_template:
    :param organization_uuid:
    :return:
    """
    result = {}
    for station_code, dates in data_template.items():
        result[station_code] = {}
        hydro_station = parsed_data["stations"][station_code]["hydro_station_obj"]

        for date in dates:
            smart_datetime = SmartDatetime(date, hydro_station, local=True)
            result[station_code][date] = data_template[station_code][date]
            wl_morning_new = result[station_code][date]["morning"].water_level_new
            wl_evening_new = result[station_code][date]["evening"].water_level_new

            discharge_average_new = None
            discharge_model = get_discharge_model_from_timestamp(
                station=hydro_station, timestamp=smart_datetime.midday_utc
            )
            if None not in [wl_morning_new, wl_evening_new]:
                wl_average_new = custom_ceil((wl_morning_new + wl_evening_new) / 2)
                discharge_average_new = discharge_model.estimate_discharge(wl_average_new)
            elif wl_morning_new is None and wl_evening_new is None:
                wl_average_new = None
            else:
                wl_average_new = wl_morning_new or wl_evening_new
                discharge_average_new = discharge_model.estimate_discharge(wl_average_new)

            result[station_code][date]["average"].water_level_new = wl_average_new
            result[station_code][date]["average"].discharge_new = custom_round(discharge_average_new, 1)

    return result


def generate_daily_overview(parsed_data: dict):
    daily_overview = []
    for station_data in parsed_data["stations"].values():
        hydro_station = station_data["hydro_station_obj"]
        for decoded in station_data["telegrams"]:
            telegram_day_smart = decoded["telegram_day_smart"]

            water_level_query_manager_result = (
                TimeseriesQueryManager(
                    HydrologicalMetric,
                    organization_uuid=hydro_station.site.organization.uuid,
                    filter_dict={
                        "timestamp": telegram_day_smart.previous_morning_utc,
                        "metric_name": HydrologicalMetricName.WATER_LEVEL_DAILY,
                        "station": hydro_station,
                        "value_type": HydrologicalMeasurementType.MANUAL,
                    },
                )
                .execute_query()
                .first()
            )
            section_one = decoded["section_one"]
            previous_day_morning_water_level = custom_round(
                getattr(water_level_query_manager_result, "avg_value", None)
            )
            previous_day_water_level_average = None
            trend_ok = False
            if previous_day_morning_water_level is not None:
                previous_day_water_level_average = round(
                    0.5 * (float(previous_day_morning_water_level) + float(section_one["water_level_20h_period"]))
                )
                trend_ok = (previous_day_morning_water_level + section_one["water_level_trend"]) == section_one[
                    "morning_water_level"
                ]

            overview_entry = {
                "station_code": decoded["section_zero"]["station_code"],
                "station_name": decoded["section_zero"]["station_name"],
                "telegram_day_date": telegram_day_smart.local.date().isoformat(),
                "previous_day_date": telegram_day_smart.previous_local.date().isoformat(),
                "section_one": decoded.get("section_one", None),
                "calc_trend_ok": trend_ok,
                "calc_previous_day_water_level_average": previous_day_water_level_average,
                "db_previous_day_morning_water_level": previous_day_morning_water_level,
                "section_three": decoded.get("section_three", None),
                "section_six": decoded.get("section_six", []),
                "section_eight": decoded.get("section_eight", None),
            }
            daily_overview.append(overview_entry)
    return daily_overview


def simulate_telegram_insertion(parsed_data: dict) -> dict:
    initial_template = {}

    for station_code, station_data in parsed_data["stations"].items():
        initial_template[station_code] = {}
        for telegram_data in station_data["telegrams"]:
            telegram_day_smart = telegram_data["telegram_day_smart"]
            telegram_day_date = telegram_day_smart.local.date().isoformat()
            previous_day_date = telegram_day_smart.previous_local.date().isoformat()
            initial_template[station_code][telegram_day_date] = initial_template[station_code][previous_day_date] = {
                "morning": {},
                "evening": {},
                "average": {},
            }

    template_filled_old = fill_template_with_old_metrics(initial_template, parsed_data)
    template_filled_morning_evening = insert_template_with_new_metrics(template_filled_old, parsed_data)

    template_filled_averages = insert_new_averages(template_filled_morning_evening, parsed_data)
    return template_filled_averages


def generate_reported_discharge_points(parsed_data: dict) -> dict:
    """
    Gather all the water level/discharge from telegrams and group them based on the station code.
    :param parsed_data:
    :return:
    """
    reported_discharge_points = {}
    index = 0
    for station_code, station_data in parsed_data["stations"].items():
        reported_discharge_points[station_code] = []
        for decoded in station_data["telegrams"]:
            for entry in decoded.get("section_six", []):
                reported_discharge_points[station_code].append(
                    {
                        "id": index,
                        "date": entry["date"],
                        "h": entry["water_level"],
                        "q": entry["discharge"],
                    }
                )
                index = index + 1
    return reported_discharge_points


def generate_data_processing_overview(simulation_result: dict) -> dict:
    # make station codes as keys and list of sorted date entries as their values
    result_sorted_by_date = {}
    for station_code, station_data in simulation_result.items():
        date_entries_list = []
        for key, value in station_data.items():
            date_entries_list.append((key, value))
        sorted_entries_list = sorted(date_entries_list, key=lambda x: x[0])  # sort by date
        result_sorted_by_date[station_code] = sorted_entries_list
    return result_sorted_by_date


def generate_save_data_overview(parsed_data: dict, simulation_result: str) -> list:
    save_data_overview = []

    for station_code, station_data in parsed_data["stations"].items():
        for telegram_data in station_data["telegrams"]:
            item = {}
            telegram_day_smart = telegram_data["telegram_day_smart"]
            telegram_day_date = telegram_day_smart.local.date().isoformat()
            previous_day_date = telegram_day_smart.previous_local.date().isoformat()
            item["station_code"] = station_code
            item["station_name"] = telegram_data["section_zero"]["station_name"]
            item["telegram_day_date"] = telegram_day_date
            item["previous_day_date"] = previous_day_date
            item["previous_day_data"] = simulation_result[station_code][previous_day_date]
            item["telegram_day_data"] = simulation_result[station_code][telegram_day_date]
            item["section_one"] = telegram_data.get("section_one")
            item["section_six"] = telegram_data.get("section_six", [])
            item["section_eight"] = telegram_data.get("section_eight")
            telegram_type = ""
            if telegram_data.get("section_one"):
                telegram_type += "discharge"
            if telegram_data.get("section_eight"):
                telegram_type += " / meteo" if telegram_type else "meteo"
            item["type"] = telegram_type  # TODO determine if discharge / meteo or both or single
            save_data_overview.append(item)
    return save_data_overview
