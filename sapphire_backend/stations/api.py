from django.db import IntegrityError
from django.utils.translation import gettext as _
from ninja import Query
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.organizations.models import Organization
from sapphire_backend.utils.mixins.schemas import Message
from sapphire_backend.utils.permissions import IsOrganizationAdmin, IsSuperAdmin, OrganizationExists

from .models import Station
from .schema import (
    StationFilterSchema,
    StationInputSchema,
    StationOutputDetailSchema,
    StationUpdateSchema,
)


@api_controller(
    "stations/{organization_uuid}",
    tags=["Stations"],
    auth=JWTAuth(),
    permissions=[OrganizationExists & (IsOrganizationAdmin | IsSuperAdmin)],
)
class StationsAPIController:
    @route.post("", response={201: StationOutputDetailSchema, 400: Message})
    def create_station(self, request, organization_uuid: str, station_data: StationInputSchema):
        try:
            organization = Organization.objects.get(uuid=organization_uuid)
            station_dict = station_data.dict()
            station_dict["organization"] = organization
            station = Station.objects.create(**station_dict)
        except IntegrityError:
            return 400, {"detail": _("Station with the same code already exists."), "code": "duplicate_station"}

        return 201, station

    @route.get("", response=list[StationOutputDetailSchema])
    def get_stations(self, request, organization_uuid: str, station_type_filter: StationFilterSchema = Query(...)):
        stations = Station.objects.filter(organization__uuid=organization_uuid, is_deleted=False)
        if station_type_filter.station_type:
            stations = stations.filter(station_type=station_type_filter.station_type.value)

        return stations.select_related("organization")

    @route.get("stats")
    def get_stations_stats(self, request, organization_uuid: str):
        stats = {}
        stations = Station.objects.filter(organization__uuid=organization_uuid, is_deleted=False)

        station_type = Station.StationType

        stats["cnt_total"] = stations.count()
        stats["cnt_manual"] = stations.filter(is_automatic=False).count()
        stats["cnt_auto"] = stations.filter(is_automatic=True).count()
        stats["cnt_hydro_total"] = stations.filter(station_type=station_type.HYDROLOGICAL.value).count()
        stats["cnt_hydro_auto"] = stations.filter(
            station_type=station_type.HYDROLOGICAL.value, is_automatic=True
        ).count()
        stats["cnt_hydro_manual"] = stations.filter(
            station_type=station_type.HYDROLOGICAL.value, is_automatic=False
        ).count()
        stats["cnt_meteo_total"] = stations.filter(station_type=station_type.METEOROLOGICAL.value).count()
        stats["cnt_meteo_auto"] = stations.filter(
            station_type=station_type.METEOROLOGICAL.value, is_automatic=True
        ).count()
        stats["cnt_meteo_manual"] = stations.filter(
            station_type=station_type.METEOROLOGICAL.value, is_automatic=False
        ).count()

        return stats

    @route.get("{station_uuid}", response={200: StationOutputDetailSchema, 404: Message})
    def get_station(self, request, organization_uuid: str, station_uuid: str):
        try:
            return 200, Station.objects.get(uuid=station_uuid, is_deleted=False)
        except Station.DoesNotExist:
            return 404, {"detail": _("Station not found."), "code": "not_found"}

    @route.delete("{station_uuid}", response={200: Message, 400: Message, 404: Message})
    def delete_station(self, request, organization_uuid: str, station_uuid: str):
        try:
            station = Station.objects.get(uuid=station_uuid, is_deleted=False)
            station.is_deleted = True
            station.save()
            return 200, {"detail": _(f"{station.name} station successfully deleted"), "code": "success"}
        except Station.DoesNotExist:
            return 404, {"detail": _("Station not found."), "code": "not_found"}
        except IntegrityError:
            return 400, {"detail": _("Station could not be deleted."), "code": "error"}

    @route.put("{station_uuid}", response={200: StationOutputDetailSchema, 404: Message})
    def update_station(self, request, organization_uuid: str, station_uuid: str, station_data: StationUpdateSchema):
        try:
            station = Station.objects.get(uuid=station_uuid, is_deleted=False)
            for attr, value in station_data.dict(exclude_unset=True).items():
                setattr(station, attr, value)
            station.save()
            return 200, station
        except Station.DoesNotExist:
            return 404, {"detail": _("Station not found."), "code": "not_found"}
