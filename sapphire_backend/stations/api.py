from django.db import IntegrityError
from django.db.models import Q
from django.db.models.aggregates import Count
from django.http import HttpRequest
from django.utils.translation import gettext as _
from ninja import Query
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.utils.mixins.schemas import Message
from sapphire_backend.utils.permissions import (
    admin_permissions,
    regular_permissions,
)

from .models import HydrologicalStation, MeteorologicalStation, Remark, Site
from .schema import (
    HydrologicalStationFilterSchema,
    HydrologicalStationStatsSchema,
    HydroStationInputSchema,
    HydroStationOutputDetailSchema,
    HydroStationUpdateSchema,
    MeteoStationOutputDetailSchema,
    MeteoStationStatsSchema,
    RemarkInputSchema,
    RemarkOutputSchema,
)


@api_controller(
    "stations/{organization_uuid}/hydrological",
    tags=["Hydrological stations"],
    auth=JWTAuth(),
    permissions=regular_permissions,
)
class HydroStationsAPIController:
    @route.post("", response={201: HydroStationOutputDetailSchema, 400: Message})
    def create_hydrological_station(
        self, request: HttpRequest, organization_uuid: str, station_data: HydroStationInputSchema
    ):
        try:
            station_dict = station_data.dict()
            site_uuid = station_dict.pop("site_uuid", None)
            site_data = station_dict.pop("site_data", {})
            if not site_uuid:
                site_data["organization_id"] = organization_uuid
                site = Site.objects.create(**site_data)
                station_dict["site_id"] = site.uuid
            else:
                station_dict["site_id"] = site_uuid
                site = Site.objects.get(uuid=site_uuid)

            station = HydrologicalStation.objects.create(**station_dict)
        except IntegrityError:
            return 400, {
                "detail": _("Hydrological station with the same code already exists."),
                "code": "duplicate_station",
            }

        return 201, station

    @route.get("", response=list[HydroStationOutputDetailSchema])
    def get_hydrological_stations(
        self,
        request: HttpRequest,
        organization_uuid: str,
        filters: Query[HydrologicalStationFilterSchema],
    ):
        stations = (
            HydrologicalStation.objects.for_organization(organization_uuid)
            .active()
            .filter(**filters.dict(exclude_unset=True))
        )
        return stations.select_related("site", "site__organization", "site__region", "site__basin")

    @route.get("stats", response={200: HydrologicalStationStatsSchema})
    def get_hydrological_stations_stats(self, request: HttpRequest, organization_uuid: str):
        station_type = HydrologicalStation.StationType
        stations = HydrologicalStation.objects.for_organization(organization_uuid).active()
        stats_aggr = stations.aggregate(
            total=Count("id"),
            manual=Count("id", filter=Q(station_type=station_type.MANUAL)),
            auto=Count("id", filter=Q(station_type=station_type.AUTOMATIC)),
        )

        return stats_aggr

    @route.get("{station_uuid}", response={200: HydroStationOutputDetailSchema, 404: Message})
    def get_hydrological_station(self, request: HttpRequest, organization_uuid: str, station_uuid: str):
        try:
            return 200, HydrologicalStation.objects.get(uuid=station_uuid, is_deleted=False)
        except HydrologicalStation.DoesNotExist:
            return 404, {"detail": _("Station not found."), "code": "not_found"}

    @route.delete("{station_uuid}", response={200: Message, 400: Message, 404: Message}, permissions=admin_permissions)
    def delete_hydrological_station(self, request: HttpRequest, organization_uuid: str, station_uuid: str):
        try:
            station = HydrologicalStation.objects.get(uuid=station_uuid, is_deleted=False)
            station.is_deleted = True
            station.save()
            return 200, {"detail": _(f"{station.name} station successfully deleted"), "code": "success"}
        except HydrologicalStation.DoesNotExist:
            return 404, {"detail": _("Station not found."), "code": "not_found"}
        except IntegrityError:
            return 400, {"detail": _("Station could not be deleted."), "code": "error"}

    @route.put("{station_uuid}", response={200: HydroStationOutputDetailSchema, 404: Message})
    def update_station(
        self, request: HttpRequest, organization_uuid: str, station_uuid: str, station_data: HydroStationUpdateSchema
    ):
        try:
            station = HydrologicalStation.objects.get(uuid=station_uuid, is_deleted=False)
            station_dict = station_data.dict(exclude_unset=True)
            site_data = station_dict.pop("site_data", {})
            if site_data:
                site = station.site
                for attr, value in site_data.items():
                    setattr(site, attr, value)
                site.save()

            for attr, value in station_dict.items():
                setattr(station, attr, value)

            station.save()
            return 200, station
        except HydrologicalStation.DoesNotExist:
            return 404, {"detail": _("Station not found."), "code": "not_found"}

    @route.post("{station_uuid}/remarks", response={200: RemarkOutputSchema})
    def create_remark(
        self, request: HttpRequest, organization_uuid: str, station_uuid: str, remark_data: RemarkInputSchema
    ):
        remark_dict = remark_data.dict()
        remark_dict["user"] = request.user
        remark_dict["hydro_station_id"] = station_uuid

        remark = Remark.objects.create(**remark_dict)

        return remark

    @route.delete("remarks/{remark_uuid}", response={200: Message})
    def delete_remark(self, request: HttpRequest, organization_uuid: str, remark_uuid: str):
        try:
            Remark.objects.filter(uuid=remark_uuid).delete()
            return 200, {"detail": _("Remark deleted successfully"), "code": "success"}
        except IntegrityError:
            return 400, {"detail": _("Remark could not be deleted"), "code": "error"}


@api_controller(
    "stations/{organization_uuid}/meteo",
    tags=["Meteorological stations"],
    auth=JWTAuth(),
    permissions=regular_permissions,
)
class MeteoStationsAPIController:
    @route.get("", response=list[MeteoStationOutputDetailSchema])
    def get_meteorological_stations(self, request: HttpRequest, organization_uuid: str):
        stations = MeteorologicalStation.objects.for_organization(organization_uuid).active()
        return stations.select_related("site", "site__organization")

    @route.get("stats", response=MeteoStationStatsSchema)
    def get_meteorological_stations_stats(self, request: HttpRequest, organization_uuid: str):
        return MeteorologicalStation.objects.for_organization(organization_uuid).active().aggregate(total=Count("id"))
