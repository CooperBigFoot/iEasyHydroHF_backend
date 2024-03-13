import logging
from datetime import datetime

from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.utils.datetime_helper import to_utc, yesterday_date, yesterday_morning
from sapphire_backend.utils.mixins.schemas import Message
from sapphire_backend.utils.permissions import IsOrganizationMember, IsSuperAdmin, OrganizationExists
from sapphire_backend.metrics.choices import (
    HydrologicalMeasurementType,
    HydrologicalMetricName,
    MeteorologicalMeasurementType,
    MeteorologicalMetricName,
    MetricUnit,
)

from .exceptions import TelegramParserException
from .parser import KN15TelegramParser
from .schema import BulkParseOutputSchema, TelegramBulkInputSchema, TelegramInputSchema, TelegramOutputSchema, \
    TelegramBulkWithDatesInputSchema, DailyOverviewOutputSchema
from ..metrics.models import HydrologicalMetric


@api_controller(
    "telegrams/{organization_uuid}",
    tags=["Telegrams"],
    auth=JWTAuth(),
    permissions=[OrganizationExists & IsOrganizationMember | IsSuperAdmin],
)
class TelegramsAPIController:
    @route.post("parse", response={201: TelegramOutputSchema, 400: Message})
    def parse_telegram(self, request, organization_uuid: str, encoded_telegram: TelegramInputSchema):
        parser = KN15TelegramParser(encoded_telegram.telegram)
        try:
            decoded = parser.parse()
            if str(parser.station.organization.uuid) != organization_uuid:
                return 400, {
                    "detail": f"Station with code {parser.station.station_code} does not exist for this organization",
                    "code": "invalid_station",
                }
            return 201, decoded
        except TelegramParserException as e:
            return 400, {"detail": str(e), "code": "invalid_telegram"}

    @route.post("parse-bulk", response={201: BulkParseOutputSchema, 400: Message})
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
                    hydro_station_org_uuid = str(getattr(parser.hydro_station.site.organization, 'uuid'))
                    hydro_station_code = parser.hydro_station.station_code
                if parser.exists_meteo_station:
                    meteo_station_org_uuid = str(getattr(parser.meteo_station.site.organization, 'uuid'))
                    meteo_station_code = parser.meteo_station.station_code
                if organization_uuid not in [hydro_station_org_uuid, meteo_station_org_uuid]:
                    error = f"Station with code {hydro_station_code or meteo_station_code} does not exist for this organization"
                    data["errors"].append({"index": idx, "telegram": telegram, "error": error})
                    parser.save_parsing_error(error)

                daily_discharge_entry = {
                    "previous_day": {

                    },
                    "telegram_day":
                        {

                        }
                }

                data["processed"].append({"index": idx, "telegram": telegram,

                                          "parsed_data": decoded})
            except TelegramParserException as e:
                data["errors"].append({"index": idx, "telegram": telegram, "error": str(e)})

        return 201, data

    @route.post("get-daily-overview", response={201: DailyOverviewOutputSchema, 400: Message})
    def get_daily_overview(self, request, organization_uuid: str,
                           encoded_telegrams_dates: TelegramBulkWithDatesInputSchema):
        data = {"parsed": [], "errors": []}
        discharge_overview = []
        meteo_overview = []
        hydro_station_codes = set()
        meteo_station_codes = set()

        for idx, telegram_date in enumerate(encoded_telegrams_dates.telegrams):
            telegram = telegram_date.raw
            override_date = telegram_date.override_date  # TODO conversion format do it here -> datetime
            parser = KN15TelegramParser(telegram)
            try:
                decoded = parser.parse()
                hydro_station_code = None
                meteo_station_code = None
                hydro_station_org_uuid = None
                meteo_station_org_uuid = None
                if parser.exists_hydro_station:
                    hydro_station_org_uuid = str(getattr(parser.hydro_station.site.organization, 'uuid'))
                    hydro_station_code = parser.hydro_station.station_code
                    hydro_station_codes.add((hydro_station_code,  parser.hydro_station.id))
                if parser.exists_meteo_station:
                    meteo_station_org_uuid = str(getattr(parser.meteo_station.site.organization, 'uuid'))
                    meteo_station_code = parser.meteo_station.station_code
                if organization_uuid not in [hydro_station_org_uuid, meteo_station_org_uuid]:
                    error = f"Station with code {hydro_station_code or meteo_station_code} does not exist for this organization"
                    data["errors"].append({"index": idx, "telegram": telegram, "error": error})
                    parser.save_parsing_error(error)

                # data["parsed"].append({"index": idx, "telegram": telegram, "parsed_data": decoded})
            except TelegramParserException as e:
                data["errors"].append({"index": idx, "telegram": telegram, "error": str(e)})
                logging.exception(e)

            if decoded.get("section_one", False):
                telegram_morning_dt_local = datetime.fromisoformat(decoded["section_zero"]["date"])
                if override_date is not None:
                    telegram_morning_dt_local = datetime.fromisoformat(override_date)
                telegram_day_morning_water_level = decoded["section_one"]["morning_water_level"]
                telegram_day_water_level_trend = decoded["section_one"]["water_level_trend"]
                previous_day_dt_local = yesterday_date(telegram_morning_dt_local)
                previous_day_morning_dt_local = yesterday_morning(telegram_morning_dt_local)
                previous_day_evening_water_level = decoded["section_one"]["water_level_20h_period"]
                try:
                    HydrologicalMetric(timestamp=to_utc(previous_day_morning_dt_local),
                                       station=parser.hydro_station,
                                       metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
                                       value_type=HydrologicalMeasurementType.MANUAL,
                                       avg_value=150.0).save(refresh_view=False)  # TODO REMOVE AND HANDLE WHEN EMPTY
                except Exception as e:
                    print(e)
                previous_day_morning_water_level = HydrologicalMetric(timestamp=to_utc(previous_day_morning_dt_local),
                                                                      station=parser.hydro_station,
                                                                      metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
                                                                      value_type=HydrologicalMeasurementType.MANUAL).select_first().avg_value
                previous_day_water_level_average = (
                                                       previous_day_morning_water_level + previous_day_evening_water_level) / 2
                trend_ok = (
                               previous_day_morning_water_level + telegram_day_water_level_trend) == telegram_day_water_level_trend
                entry = {
                    "index": idx,
                    "station_code": decoded["section_zero"]["station_code"],
                    "station_name": decoded["section_zero"]["station_name"],
                    "telegram_day_date": telegram_morning_dt_local.date().isoformat(),
                    "telegram_day_morning_water_level": telegram_day_morning_water_level,
                    "telegram_day_water_level_trend": telegram_day_water_level_trend,
                    "trend_ok": trend_ok,
                    "previous_day_date": previous_day_dt_local.isoformat(),
                    "previous_day_morning_water_level": previous_day_morning_water_level,
                    "previous_day_evening_water_level": previous_day_evening_water_level,
                    "previous_day_water_level_average": previous_day_water_level_average,
                    "reported_discharge": []
                }

            if decoded.get("section_six", False):
                """
                {'water_level': 253, 'discharge': 136, 'cross_section_area': 52.1, 'maximum_depth': 162, 'date': '2023-06-03T13:00:00+06:00'}
                """
                for discharge_entry in decoded["section_six"]:
                    overview_entry = {}
                    overview_entry["water_level"] = discharge_entry.get("water_level")
                    overview_entry["discharge"] = discharge_entry.get("discharge")
                    overview_entry["cross_section_area"] = discharge_entry.get("cross_section_area")
                    overview_entry["maximum_depth"] = discharge_entry.get("maximum_depth")
                    discharge_date = datetime.fromisoformat(discharge_entry.get("date"))
                    overview_entry["date"] = discharge_date.date().isoformat()
                    entry["reported_discharge"].append(overview_entry)
            discharge_overview.append(entry)
            if decoded.get("section_eight", False):
                meteo_overview.append({})
                meteo_station_codes.add({'station_code': meteo_station_code, 'station_id': parser.meteo_station.id})  #include only codes which have section 988

        data = {'discharge': discharge_overview, 'discharge_codes': list(hydro_station_codes),
                'meteo': meteo_overview, 'meteo_codes': list(meteo_station_codes) }
        return 201, data
