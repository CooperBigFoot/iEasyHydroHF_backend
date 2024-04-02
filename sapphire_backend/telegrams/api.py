import logging
from datetime import datetime

from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.metrics.choices import (
    HydrologicalMeasurementType,
    HydrologicalMetricName,
    MetricUnit,
)
from sapphire_backend.utils.datetime_helper import SmartDatetime
from sapphire_backend.utils.permissions import IsOrganizationMember, IsSuperAdmin, OrganizationExists

from ..metrics.models import HydrologicalMetric
from ..metrics.timeseries.query import TimeseriesQueryManager
from ..stations.models import HydrologicalStation
from ..utils.mixins.schemas import Message
from .exceptions import TelegramParserException
from .parser import KN15TelegramParser
from .schema import (
    BulkParseOutputSchema,
    DailyOverviewOutputSchema,
    TelegramBulkInputSchema,
    TelegramBulkWithDatesInputSchema,
    TelegramInputSchema,
    TelegramOutputSchema,
)
from .utils import (
    build_data_processing_structure,
    fill_with_old_metrics,
    insert_new_averages,
    insert_new_metrics,
    save_reported_discharge,
)


@api_controller(
    "telegrams/{organization_uuid}",
    tags=["Telegrams"],
    auth=JWTAuth(),
    permissions=[OrganizationExists & IsOrganizationMember | IsSuperAdmin],
)
class TelegramsAPIController:
    @route.post("parse", response={201: TelegramOutputSchema})
    def parse_telegram(self, request, organization_uuid: str, encoded_telegram: TelegramInputSchema):
        parser = KN15TelegramParser(encoded_telegram.telegram)
        decoded = parser.parse()
        if str(parser.station.organization.uuid) != organization_uuid:
            return 400, {
                "detail": f"Station with code {parser.station.station_code} does not exist for this organization",
                "code": "invalid_station",
            }
        return 201, decoded

    @route.post("parse-bulk", response={201: BulkParseOutputSchema})
    def bulk_parse_telegram(self, request, organization_uuid: str, encoded_telegrams: TelegramBulkInputSchema):
        data = {"parsed": [], "errors": []}
        for idx, telegram in enumerate(encoded_telegrams.telegrams):
            parser = KN15TelegramParser(telegram)
            try:
                decoded = parser.parse()
                hydro_station_code = None
                meteo_station_code = None
                hydro_station_org_uuid = None
                meteo_station_org_uuid = None
                if parser.exists_hydro_station:
                    hydro_station_org_uuid = str(parser.hydro_station.site.organization.uuid)
                    hydro_station_code = parser.hydro_station.station_code
                if parser.exists_meteo_station:
                    meteo_station_org_uuid = str(parser.meteo_station.site.organization.uuid)
                    meteo_station_code = parser.meteo_station.station_code
                if organization_uuid not in [hydro_station_org_uuid, meteo_station_org_uuid]:
                    error = f"Station with code {hydro_station_code or meteo_station_code} does not exist for this organization"
                    data["errors"].append({"index": idx, "telegram": telegram, "error": error})
                    parser.save_parsing_error(error)

                data["processed"].append({"index": idx, "telegram": telegram, "parsed_data": decoded})
            except TelegramParserException as e:
                data["errors"].append({"index": idx, "telegram": telegram, "error": str(e)})

        return 201, data

    @route.post("get-daily-overview", response={201: DailyOverviewOutputSchema, 400: Message})
    def get_daily_overview(
        self, request, organization_uuid: str, encoded_telegrams_dates: TelegramBulkWithDatesInputSchema
    ):
        data = {"parsed": [], "errors": []}
        data_overview = []
        hydro_station_codes = set()
        meteo_station_codes = set()

        for idx, telegram_date in enumerate(encoded_telegrams_dates.telegrams):
            telegram = telegram_date.raw
            override_date = telegram_date.override_date
            parser = KN15TelegramParser(telegram, organization_uuid=organization_uuid)
            try:
                decoded = parser.parse()
            except TelegramParserException as e:
                data["errors"].append({"index": idx, "telegram": telegram, "error": str(e)})
                logging.exception(e)

            telegram_day_smart = SmartDatetime(decoded["section_zero"]["date"], parser.hydro_station, local=True)
            if override_date is not None:
                telegram_day_smart = SmartDatetime(override_date, parser.hydro_station, local=True)

            overview_entry = {
                "index": idx,
                "station_code": decoded["section_zero"]["station_code"],
                "station_name": decoded["section_zero"]["station_name"],
                "telegram_day_date": telegram_day_smart.local.date().isoformat(),
                "previous_day_date": telegram_day_smart.previous_local.date().isoformat(),
                "section_one": {},
                "reported_discharge": [],
                "meteo": {},
            }

            if decoded.get("section_one", False):
                hydro_station_codes.add(
                    (parser.hydro_station.station_code, parser.hydro_station.id)
                )  # include only codes which have section 988
                telegram_day_morning_water_level = decoded["section_one"]["morning_water_level"]
                telegram_day_water_level_trend = decoded["section_one"]["water_level_trend"]
                previous_day_evening_water_level = decoded["section_one"]["water_level_20h_period"]

                water_level_query_manager_result = (
                    TimeseriesQueryManager(
                        HydrologicalMetric,
                        organization_uuid=organization_uuid,
                        filter_dict={
                            "timestamp": telegram_day_smart.previous_morning_utc,
                            "metric_name": HydrologicalMetricName.WATER_LEVEL_DAILY,
                            "station": parser.hydro_station,
                            "value_type": HydrologicalMeasurementType.MANUAL,
                        },
                    )
                    .execute_query()
                    .first()
                )
                previous_day_morning_water_level = None
                previous_day_water_level_average = None
                trend_ok = False
                if water_level_query_manager_result is not None:
                    previous_day_morning_water_level = water_level_query_manager_result.avg_value
                    previous_day_water_level_average = round(
                        0.5 * (float(previous_day_morning_water_level) + float(previous_day_evening_water_level))
                    )
                    trend_ok = (
                        previous_day_morning_water_level + telegram_day_water_level_trend
                    ) == telegram_day_morning_water_level

                overview_entry["section_one"]["telegram_day_morning_water_level"] = telegram_day_morning_water_level
                overview_entry["section_one"]["telegram_day_water_level_trend"] = telegram_day_water_level_trend
                overview_entry["section_one"]["trend_ok"] = trend_ok
                overview_entry["section_one"]["previous_day_morning_water_level"] = previous_day_morning_water_level
                overview_entry["section_one"]["previous_day_evening_water_level"] = previous_day_evening_water_level
                overview_entry["section_one"]["previous_day_water_level_average"] = previous_day_water_level_average

            if decoded.get("section_six", False):
                for discharge_entry in decoded["section_six"]:
                    reported_discharge = {}
                    discharge_date = datetime.fromisoformat(discharge_entry.get("date"))
                    reported_discharge["water_level"] = discharge_entry.get("water_level")
                    reported_discharge["discharge"] = discharge_entry.get("discharge")
                    reported_discharge["cross_section_area"] = discharge_entry.get("cross_section_area")
                    reported_discharge["maximum_depth"] = discharge_entry.get("maximum_depth")
                    reported_discharge["date"] = discharge_date.isoformat()
                    overview_entry["reported_discharge"].append(reported_discharge)

            if decoded.get("section_eight", False):
                overview_entry["meteo"] = {}
                meteo_station_code = parser.meteo_station.station_code
                meteo_station_codes.add(
                    (meteo_station_code, parser.meteo_station.id)
                )  # include only codes which have section 988

            data_overview.append(overview_entry)

        data = {
            "data": data_overview,
            "discharge_codes": list(hydro_station_codes),
            "meteo_codes": list(meteo_station_codes),
        }
        return 201, data

    @route.post("get-data-processing-overview", response={201: dict, 400: Message})
    def get_data_procesing_overview(
        self, request, organization_uuid: str, encoded_telegrams_dates: TelegramBulkWithDatesInputSchema
    ):
        data = self.get_daily_overview(request, organization_uuid, encoded_telegrams_dates)

        if not data[0] == 201:
            return data
        parsed_data_list = data[1]["data"]

        initial_struct = build_data_processing_structure(parsed_data_list)

        template_filled_old = fill_with_old_metrics(initial_struct, organization_uuid)
        template_filled_morning_evening = insert_new_metrics(template_filled_old, parsed_data_list, organization_uuid)
        template_filled_averages = insert_new_averages(template_filled_morning_evening, organization_uuid)
        result = template_filled_averages

        # make station codes as keys and list of sorted date entries as their values
        result_sorted = {}
        for station_code, station_data in result.items():
            date_entries_list = []
            for key, value in station_data.items():
                date_entries_list.append((key, value))
            sorted_entries_list = sorted(date_entries_list, key=lambda x: x[0])  # sort by date
            result_sorted[station_code] = sorted_entries_list

        return 201, result_sorted

    @route.post("get-save-data-overview", response={201: list, 400: Message})
    def get_save_data_overview(
        self, request, organization_uuid: str, encoded_telegrams_dates: TelegramBulkWithDatesInputSchema
    ):
        resp_code, daily_overview = self.get_daily_overview(request, organization_uuid, encoded_telegrams_dates)
        if not resp_code == 201:
            return resp_code, daily_overview

        resp_code, data_processing_overview = self.get_data_procesing_overview(
            request, organization_uuid, encoded_telegrams_dates
        )
        if not resp_code == 201:
            return resp_code, data_processing_overview
        result_overview = []

        data_processing_dict = {}
        for station_code, station_data_list in data_processing_overview.items():
            data_processing_dict[station_code] = {}
            for date, station_data in station_data_list:
                data_processing_dict[station_code][date] = station_data

        for telegram_entry in daily_overview["data"]:
            item = {}
            station_code = telegram_entry["station_code"]
            previous_day_date = telegram_entry["previous_day_date"]
            telegram_day_date = telegram_entry["telegram_day_date"]
            item["station_code"] = station_code
            item["station_name"] = telegram_entry["station_name"]
            item["telegram_day_date"] = telegram_day_date
            item["previous_day_date"] = previous_day_date
            item["previous_day_data"] = data_processing_dict[station_code][previous_day_date]
            item["telegram_day_data"] = data_processing_dict[station_code][telegram_day_date]
            item["reported_discharge"] = telegram_entry.get("reported_discharge")
            item["meteo_data"] = telegram_entry.get("meteo_data")  # TODO
            item["temperature_data"] = telegram_entry.get("temperature_data")  # TODO
            item["type"] = "discharge / meteo ???"  # TODO determine if discharge / meteo or both or single
            result_overview.append(item)
        return 201, result_overview

    @route.post("save-input-telegrams", response={201: bool, 400: Message})
    def save_input_telegrams(
        self, request, organization_uuid: str, encoded_telegrams_dates: TelegramBulkWithDatesInputSchema
    ):
        resp_code, daily_overview = self.get_daily_overview(request, organization_uuid, encoded_telegrams_dates)
        if not resp_code == 201:
            return resp_code, daily_overview

        for telegram_entry in daily_overview["data"]:
            station_code = telegram_entry["station_code"]
            hydro_station = HydrologicalStation.objects.filter(
                station_code=station_code, station_type=HydrologicalStation.StationType.MANUAL
            ).first()

            telegram_day_date = telegram_entry["telegram_day_date"]

            smart_telegram_date = SmartDatetime(telegram_day_date, hydro_station)
            yesterday_evening_wl_metric = HydrologicalMetric(
                timestamp=smart_telegram_date.previous_evening_utc,
                min_value=None,
                avg_value=telegram_entry["section_one"]["previous_day_evening_water_level"],
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
                timestamp=smart_telegram_date.morning_utc,
                min_value=None,
                avg_value=telegram_entry["section_one"]["telegram_day_morning_water_level"],
                max_value=None,
                unit=MetricUnit.WATER_LEVEL,
                value_type=HydrologicalMeasurementType.MANUAL,
                metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
                station=hydro_station,
                sensor_identifier="",
                sensor_type="",
            )
            morning_wl_metric.save(refresh_view=True)
            reported_discharge = telegram_entry.get("reported_discharge")
            if reported_discharge is not None:
                save_reported_discharge(reported_discharge, hydro_station)
        return 201, True
