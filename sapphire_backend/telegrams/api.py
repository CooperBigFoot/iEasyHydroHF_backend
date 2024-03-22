import logging
from datetime import datetime

from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.metrics.choices import (
    HydrologicalMeasurementType,
    HydrologicalMetricName,
)
from sapphire_backend.utils.datetime_helper import SmartDatetime
from sapphire_backend.utils.permissions import IsOrganizationMember, IsSuperAdmin, OrganizationExists
from .exceptions import TelegramParserException
from .parser import KN15TelegramParser
from .schema import BulkParseOutputSchema, TelegramBulkInputSchema, TelegramInputSchema, TelegramOutputSchema, \
    TelegramBulkWithDatesInputSchema, DailyOverviewOutputSchema, DataProcessingOverviewOutputSchema, TimeData
from .utils import fill_morning_operational, fill_evening_operational, fill_average_operational
from ..metrics.models import HydrologicalMetric
from ..metrics.timeseries.query import TimeseriesQueryManager
from ..stations.models import HydrologicalStation
from ..utils.mixins.schemas import Message


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
                    hydro_station_org_uuid = str(getattr(parser.hydro_station.site.organization, 'uuid'))
                    hydro_station_code = parser.hydro_station.station_code
                if parser.exists_meteo_station:
                    meteo_station_org_uuid = str(getattr(parser.meteo_station.site.organization, 'uuid'))
                    meteo_station_code = parser.meteo_station.station_code
                if organization_uuid not in [hydro_station_org_uuid, meteo_station_org_uuid]:
                    error = f"Station with code {hydro_station_code or meteo_station_code} does not exist for this organization"
                    data["errors"].append({"index": idx, "telegram": telegram, "error": error})
                    parser.save_parsing_error(error)

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
                    hydro_station_codes.add((hydro_station_code, parser.hydro_station.id))
                if parser.exists_meteo_station:
                    meteo_station_org_uuid = str(getattr(parser.meteo_station.site.organization, 'uuid'))
                    meteo_station_code = parser.meteo_station.station_code
                if organization_uuid not in [hydro_station_org_uuid, meteo_station_org_uuid]:
                    error = f"Station with code {hydro_station_code or meteo_station_code} does not exist for this organization"
                    data["errors"].append({"index": idx, "telegram": telegram, "error": error})
                    parser.save_parsing_error(error)

            except TelegramParserException as e:
                data["errors"].append({"index": idx, "telegram": telegram, "error": str(e)})
                logging.exception(e)

            if decoded.get("section_one", False):
                telegram_day_smart = SmartDatetime(decoded["section_zero"]["date"], parser.hydro_station, local=True)
                if override_date is not None:
                    telegram_day_smart = SmartDatetime(override_date, parser.hydro_station, local=True)
                # telegram_morning_dt_local = telegram_day_smart.morning_local

                telegram_day_morning_water_level = decoded["section_one"]["morning_water_level"]
                telegram_day_water_level_trend = decoded["section_one"]["water_level_trend"]
                # previous_day_dt_local = yesterday_date(telegram_morning_dt_local)
                # previous_day_morning_dt_local = yesterday_morning(telegram_morning_dt_local)
                previous_day_evening_water_level = decoded["section_one"]["water_level_20h_period"]

                water_level_query_manager_result = TimeseriesQueryManager(HydrologicalMetric,
                                                                          organization_uuid=organization_uuid,
                                                                          filter_dict={
                                                                              "timestamp": telegram_day_smart.previous_morning_utc,
                                                                              "metric_name": HydrologicalMetricName.WATER_LEVEL_DAILY,
                                                                              "station": parser.hydro_station,
                                                                              "value_type": HydrologicalMeasurementType.MANUAL
                                                                          }, ).execute_query().first()
                previous_day_morning_water_level = None
                previous_day_water_level_average = None
                trend_ok = False
                if water_level_query_manager_result is not None:
                    previous_day_morning_water_level = water_level_query_manager_result.avg_value
                    previous_day_water_level_average = round(0.5 * (
                        float(previous_day_morning_water_level) + float(previous_day_evening_water_level)))
                    trend_ok = (
                                   previous_day_morning_water_level + telegram_day_water_level_trend) == telegram_day_water_level_trend

                entry = {
                    "index": idx,
                    "station_code": decoded["section_zero"]["station_code"],
                    "station_name": decoded["section_zero"]["station_name"],
                    "telegram_day_date": telegram_day_smart.local.date().isoformat(),
                    # telegram_morning_dt_local.date().isoformat(),
                    "telegram_day_morning_water_level": telegram_day_morning_water_level,
                    "telegram_day_water_level_trend": telegram_day_water_level_trend,
                    "trend_ok": trend_ok,
                    "previous_day_date": telegram_day_smart.previous_local.date().isoformat(),
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
                meteo_station_codes.add({'station_code': meteo_station_code,
                                         'station_id': parser.meteo_station.id})  # include only codes which have section 988

        data = {'discharge': discharge_overview, 'discharge_codes': list(hydro_station_codes),
                'meteo': meteo_overview, 'meteo_codes': list(meteo_station_codes)}
        return 201, data

    @route.post("get-data-processing-overview", response={201: dict, 400: Message})
    def get_data_procesing_overview(self, request, organization_uuid: str,
                                    encoded_telegrams_dates: TelegramBulkWithDatesInputSchema):

        data = self.get_daily_overview(request, organization_uuid, encoded_telegrams_dates)
        result = {}
        if not data[0] == 201:
            return data
        parsed_data_list = data[1]
        for parsed in parsed_data_list["discharge_codes"]:
            station_code = parsed[0]
            result[station_code] = {}

        empty_timedata = TimeData(water_level_new=None, water_level_old=None, discharge_new=None, discharge_old=None)
        for parsed in parsed_data_list["discharge"]:
            station_code = parsed["station_code"]
            telegram_day_date = parsed["telegram_day_date"]
            previous_day_date = parsed["previous_day_date"]

            result[station_code][telegram_day_date] = {'morning': empty_timedata, 'evening': empty_timedata,
                                                       'average': empty_timedata}
            result[station_code][previous_day_date] = {'morning': empty_timedata, 'evening': empty_timedata,
                                                       'average': empty_timedata}

        for parsed in parsed_data_list["discharge"]:
            station_code = parsed["station_code"]
            hydro_station = HydrologicalStation.objects.filter(station_code=station_code,
                                                               station_type=HydrologicalStation.StationType.MANUAL
                                                               ).first()
            # telegram day
            telegram_day_date = parsed["telegram_day_date"]
            # morning
            result[station_code][telegram_day_date]["morning"] = fill_morning_operational(station=hydro_station,
                                                                                          date=telegram_day_date,
                                                                                          water_level_new=parsed[
                                                                                              "telegram_day_morning_water_level"],
                                                                                          )
            # evening
            # keep the water_level_new value if it's already been filled in previous iterations
            water_level_new = result[station_code][telegram_day_date]["evening"].water_level_new
            result[station_code][telegram_day_date]["evening"] = fill_evening_operational(station=hydro_station,
                                                                                          date=telegram_day_date,
                                                                                          water_level_new=water_level_new,
                                                                                          )

            # previous day
            # morning
            previous_day_date = parsed["previous_day_date"]
            # keep the water_level_new value if it's already been filled in previous iterations
            water_level_new = result[station_code][previous_day_date]["morning"].water_level_new
            result[station_code][previous_day_date]["morning"] = fill_morning_operational(station=hydro_station,
                                                                                          date=previous_day_date,
                                                                                          water_level_new=water_level_new, )
            # evening
            previous_day_evening_water_level_new = parsed["previous_day_evening_water_level"]

            result[station_code][previous_day_date]["evening"] = fill_evening_operational(station=hydro_station,
                                                                                          date=previous_day_date,
                                                                                          water_level_new=previous_day_evening_water_level_new,
                                                                                          )

        for station_code, station_data in result.items():
            hydro_station = HydrologicalStation.objects.filter(station_code=station_code,
                                                               station_type=HydrologicalStation.StationType.MANUAL
                                                               ).first()
            for date, date_entry in station_data.items():
                for time_of_day in ['morning', 'evening']:
                    if date_entry[time_of_day].water_level_new is None:
                        result[station_code][date][time_of_day].water_level_new = date_entry[time_of_day].water_level_old
                        result[station_code][date][time_of_day].discharge_new = date_entry[time_of_day].discharge_old

                    avg_water_level_new = None
                    if None not in [date_entry["morning"].water_level_new, date_entry["evening"].water_level_new]:
                        avg_water_level_new = round(0.5 * (date_entry["morning"].water_level_new) + float(
                            date_entry["evening"].water_level_new))

                    result[station_code][date]["average"] = fill_average_operational(station=hydro_station,
                                                                     date=date,
                                                                     water_level_new=avg_water_level_new,
                                                                     )

        return 201, result
