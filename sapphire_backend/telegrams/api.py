from django.utils.translation import gettext as _
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.metrics.choices import (
    HydrologicalMeasurementType,
    HydrologicalMetricName,
    MetricUnit,
)
from sapphire_backend.utils.permissions import (
    regular_permissions,
)

from ..metrics.models import HydrologicalMetric
from ..utils.mixins.schemas import Message
from .schema import (
    TelegramBulkWithDatesInputSchema,
    TelegramOverviewOutputSchema,
)
from .utils import (
    generate_daily_overview,
    generate_data_processing_overview,
    generate_save_data_overview,
    get_parsed_telegrams_data,
    save_reported_discharge,
    simulate_telegram_insertion,
)


@api_controller(
    "telegrams/{organization_uuid}",
    tags=["Telegrams"],
    auth=JWTAuth(),
    permissions=regular_permissions,
)
class TelegramsAPIController:
    @route.post("get-telegram-overview", response={200: TelegramOverviewOutputSchema, 400: Message})
    def get_telegram_overview(
        self, request, organization_uuid: str, encoded_telegrams_dates: TelegramBulkWithDatesInputSchema
    ):
        parsed_data = get_parsed_telegrams_data(encoded_telegrams_dates, organization_uuid)
        telegram_insert_simulation_result = simulate_telegram_insertion(parsed_data)

        daily_overview = generate_daily_overview(parsed_data)
        data_processing_overview = generate_data_processing_overview(telegram_insert_simulation_result)
        save_data_overview = generate_save_data_overview(parsed_data, telegram_insert_simulation_result)

        telegram_overview = {
            "daily_overview": daily_overview,
            "data_processing_overview": data_processing_overview,
            "save_data_overview": save_data_overview,
            "discharge_codes": parsed_data["hydro_station_codes"],
            "meteo_codes": parsed_data["meteo_station_codes"],
            "errors": parsed_data["errors"],
        }
        return 200, telegram_overview

    @route.post("save-input-telegrams", response={201: Message, 400: Message})
    def save_input_telegrams(
        self, request, organization_uuid: str, encoded_telegrams_dates: TelegramBulkWithDatesInputSchema
    ):
        parsed_data = get_parsed_telegrams_data(encoded_telegrams_dates, organization_uuid)
        for station_data in parsed_data["stations"].values():
            hydro_station = station_data["hydro_station_obj"]
            # meteo_station = station_data["meteo_station_obj"]  # TODO when meteo parsing gets implemented
            for telegram_data in station_data["telegrams"]:
                telegram_day_smart = telegram_data["telegram_day_smart"]
                yesterday_evening_wl_metric = HydrologicalMetric(
                    timestamp=telegram_day_smart.previous_evening_utc,
                    min_value=None,
                    avg_value=telegram_data["section_one"]["water_level_20h_period"],
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
                    avg_value=telegram_data["section_one"]["morning_water_level"],
                    max_value=None,
                    unit=MetricUnit.WATER_LEVEL,
                    value_type=HydrologicalMeasurementType.MANUAL,
                    metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
                    station=hydro_station,
                    sensor_identifier="",
                    sensor_type="",
                )
                morning_wl_metric.save(refresh_view=True)
                reported_discharge = telegram_data.get("section_six")
                if reported_discharge is not None:
                    save_reported_discharge(reported_discharge, hydro_station)
        return 201, {"detail": _("Telegram metrics successfully saved"), "code": "success"}
