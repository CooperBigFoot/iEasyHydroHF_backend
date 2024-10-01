from datetime import timedelta

from django.utils import timezone
from django.utils.translation import gettext as _
from ninja import Query
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.utils.permissions import (
    regular_permissions,
)

from ..organizations.models import Organization
from ..stations.models import Site
from ..users.models import User
from ..utils.datetime_helper import SmartDatetime
from ..utils.mixins.schemas import Message
from .models import TelegramReceived, TelegramStored
from .schema import (
    InputAckSchema,
    TelegramBulkWithDatesInputSchema,
    TelegramOverviewOutputSchema,
    TelegramReceivedFilterSchema,
    TelegramReceivedOutputSchema,
)
from .utils import (
    generate_daily_overview,
    generate_data_processing_overview,
    generate_reported_discharge_points,
    generate_save_data_overview,
    get_parsed_telegrams_data,
    save_reported_discharge,
    save_section_eight_metrics,
    save_section_one_metrics,
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
        user = request.user
        parsed_data = get_parsed_telegrams_data(
            encoded_telegrams_dates, organization_uuid, save_telegrams=True, user=user
        )
        telegram_insert_simulation_result = simulate_telegram_insertion(parsed_data)

        daily_overview = generate_daily_overview(parsed_data)
        reported_discharge_points = generate_reported_discharge_points(parsed_data)
        data_processing_overview = generate_data_processing_overview(telegram_insert_simulation_result)
        save_data_overview = generate_save_data_overview(parsed_data, telegram_insert_simulation_result)

        telegram_overview = {
            "daily_overview": daily_overview,
            "data_processing_overview": data_processing_overview,
            "reported_discharge_points": reported_discharge_points,
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
        parsed_data = get_parsed_telegrams_data(encoded_telegrams_dates, organization_uuid, save_telegrams=False)
        for station_data in parsed_data["stations"].values():
            hydro_station = station_data["hydro_station_obj"]

            for telegram_data in station_data["telegrams"]:
                telegram_day_smart = telegram_data["telegram_day_smart"]

                stored_telegram = TelegramStored(
                    telegram=telegram_data["raw"],
                    telegram_day=telegram_day_smart.morning_local.date(),
                    station_code=telegram_data["section_zero"]["station_code"],
                    stored_by=User.objects.get(id=request.user.id),
                    organization=Organization.objects.get(uuid=organization_uuid),
                )
                stored_telegram.save()

                save_section_one_metrics(
                    telegram_day_smart,
                    section_one=telegram_data["section_one"],
                    hydro_station=hydro_station,
                    source_telegram=stored_telegram,
                )

                for section_two_entry in telegram_data.get("section_two", []):
                    save_section_one_metrics(
                        section_two_entry["date_smart"],
                        section_one=section_two_entry,
                        hydro_station=hydro_station,
                        source_telegram=stored_telegram,
                    )

                meteo_data = telegram_data.get("section_eight")
                if meteo_data is not None:
                    meteo_station = station_data["meteo_station_obj"]
                    save_section_eight_metrics(meteo_data, meteo_station, source_telegram=stored_telegram)

                reported_discharge = telegram_data.get("section_six")
                if reported_discharge is not None:
                    save_reported_discharge(reported_discharge, hydro_station, source_telegram=stored_telegram)

        return 201, {"detail": _("Telegram metrics successfully saved"), "code": "success"}

    @route.get("received/list", response={200: list[TelegramReceivedOutputSchema], 404: Message})
    def list_received_telegrams(
        self, request, organization_uuid: str, filters: Query[TelegramReceivedFilterSchema] = None
    ):
        organization = Organization.objects.get(uuid=organization_uuid)
        queryset = TelegramReceived.objects.filter(organization=organization)

        if filters.created_date:
            start_created_date_tz = SmartDatetime(
                filters.created_date, station=organization, tz_included=False
            ).day_beginning_tz
            end_created_date_tz = start_created_date_tz + timedelta(days=1) - timedelta(microseconds=1)
            queryset = queryset.filter(created_date__range=(start_created_date_tz, end_created_date_tz))

        if filters.basin_uuid is not None:
            station_codes = set()
            for site in Site.objects.filter(basin=filters.basin_uuid):
                hydro_codes = set(site.hydro_stations.values_list("station_code", flat=True))
                meteo_codes = set(site.meteo_stations.values_list("station_code", flat=True))
                station_codes = station_codes | hydro_codes | meteo_codes
            station_codes.add("")  # to include all the invalid telegrams since station code might not be known
            queryset = queryset.filter(station_code__in=station_codes)

        if filters.only_pending:
            queryset = queryset.filter(acknowledged=False)

        if filters.only_invalid:
            queryset = queryset.filter(valid=False)

        if not filters.only_invalid and isinstance(filters.station_codes, str) and len(filters.station_codes) > 0:
            list_station_codes = filters.station_codes.split(",")
            queryset = queryset.filter(station_code__in=list_station_codes)

        queryset = queryset.order_by("-created_date")
        return 200, queryset

    @route.post("received/ack", response={200: Message})
    def acknowledge_received_telegrams(self, request, organization_uuid: str, payload: InputAckSchema):
        user = request.user
        org = Organization.objects.get(uuid=organization_uuid)
        tg_received_queryset = TelegramReceived.objects.filter(id__in=payload.ids, organization=org)

        if tg_received_queryset.count() != len(payload.ids):
            raise TelegramReceived.DoesNotExist("Not all provided IDs are available.")

        tg_received_queryset.update(acknowledged=True, acknowledged_by=user, acknowledged_ts=timezone.now())
        return 200, {"detail": f"Successfully acknowledged {len(payload.ids)} received telegrams."}
