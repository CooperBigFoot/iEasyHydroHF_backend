import logging
from typing import Literal

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
from .models import HydrologicalStation, MeteorologicalStation, Remark, Site, VirtualStation, VirtualStationAssociation
from .schema import (
    HydrologicalStationFilterSchema,
    HydrologicalStationStatsSchema,
    HydroStationForecastStatusInputSchema,
    HydroStationForecastStatusOutputSchema,
    HydroStationInputSchema,
    HydroStationOutputDetailSchema,
    HydroStationUpdateSchema,
    MeteoStationInputSchema,
    MeteoStationOutputDetailSchema,
    MeteoStationStatsSchema,
    MeteoStationUpdateSchema,
    RemarkInputSchema,
    RemarkOutputSchema,
    VirtualStationAssociationInputSchema,
    VirtualStationDetailOutputSchema,
    VirtualStationInputSchema,
    VirtualStationListOutputSchema,
    VirtualStationUpdateSchema, VirtualStationForecastStatusOutputSchema, VirtualStationForecastStatusInputSchema,
)

logger = logging.getLogger("api_logger")


@api_controller(
    "stations/{organization_uuid}/hydrological",
    tags=["Hydrological stations"],
    auth=JWTAuth(),
    permissions=regular_permissions,
)
class HydroStationsAPIController:
    @route.post("", response={201: HydroStationOutputDetailSchema})
    def create_hydrological_station(
        self, request: HttpRequest, organization_uuid: str, station_data: HydroStationInputSchema
    ):
        station_dict = station_data.dict()
        site_uuid = station_dict.pop("site_uuid", None)
        site_data = station_dict.pop("site_data", {})
        if not site_uuid:
            site_data["organization_id"] = organization_uuid
            site = Site.objects.create(**site_data)
            station_dict["site_id"] = site.uuid
        else:
            station_dict["site_id"] = site_uuid

        station = HydrologicalStation.objects.create(**station_dict)

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

    @route.get("{station_uuid}", response={200: HydroStationOutputDetailSchema})
    def get_hydrological_station(self, request: HttpRequest, organization_uuid: str, station_uuid: str):
        return HydrologicalStation.objects.get(uuid=station_uuid, is_deleted=False)

    @route.delete("{station_uuid}", response={200: Message}, permissions=admin_permissions)
    def delete_hydrological_station(self, request: HttpRequest, organization_uuid: str, station_uuid: str):
        station = HydrologicalStation.objects.get(uuid=station_uuid, is_deleted=False)
        station.is_deleted = True
        station.save()
        return 200, {"detail": _(f"{station.name} station successfully deleted"), "code": "success"}

    @route.put("{station_uuid}", response={200: HydroStationOutputDetailSchema, 404: Message})
    def update_station(
        self, request: HttpRequest, organization_uuid: str, station_uuid: str, station_data: HydroStationUpdateSchema
    ):
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
        return station

    @route.get("{station_uuid}/remarks", response={200: list[RemarkOutputSchema]})
    def get_remarks(self, request: HttpRequest, organization_uuid: str, station_uuid: str):
        return Remark.objects.filter(hydro_station=station_uuid)

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
        Remark.objects.filter(uuid=remark_uuid).delete()
        return 200, {"detail": _("Remark deleted successfully"), "code": "success"}


@api_controller(
    "stations/{organization_uuid}/hydro/forecast-status",
    tags=["Forecast status for hydrological stations"],
    auth=JWTAuth(),
    permissions=regular_permissions,
)
class HydroForecastStatusAPIController:
    @route.post("bulk-toggle", response={201: list[HydroStationForecastStatusOutputSchema]})
    def bulk_toggle_forecast_status(
        self,
        request: HttpRequest,
        organization_uuid: str,
        action: Query[Literal["on", "off"]],
        station_uuids: list[str],
    ):
        status = action == "on"
        stations = (
            HydrologicalStation.objects.for_organization(organization_uuid).active().filter(uuid__in=station_uuids)
        )
        _ = stations.update(
            daily_forecast=status,
            pentad_forecast=status,
            decadal_forecast=status,
            monthly_forecast=status,
            seasonal_forecast=status,
        )
        return 201, stations

    @route.get("", response=list[HydroStationForecastStatusOutputSchema])
    def get_hydrological_stations_forecast_status(self, request: HttpRequest, organization_uuid: str):
        return HydrologicalStation.objects.for_organization(organization_uuid).active()

    @route.get("{station_uuid}", response=HydroStationForecastStatusOutputSchema)
    def get_single_hydrological_station_forecast_status(
        self, request: HttpRequest, organization_uuid: str, station_uuid: str
    ):
        return HydrologicalStation.objects.get(uuid=station_uuid, is_deleted=False)

    @route.post("{station_uuid}", response={201: HydroStationForecastStatusOutputSchema})
    def set_hydrological_station_forecast_status(
        self,
        request: HttpRequest,
        organization_uuid: str,
        station_uuid: str,
        forecast_data: HydroStationForecastStatusInputSchema,
    ):
        station = HydrologicalStation.objects.get(uuid=station_uuid, is_deleted=False)
        for forecast, value in forecast_data.dict().items():
            setattr(station, forecast, value)

        station.save()

        return 201, station


@api_controller(
    "stations/{organization_uuid}/virtual/forecast-status",
    tags=["Forecast status for virtual stations"],
    auth=JWTAuth(),
    permissions=regular_permissions,
)
class VirtualForecastStatusAPIController:
    @route.post("bulk-toggle", response={201: list[VirtualStationForecastStatusOutputSchema]})
    def bulk_toggle_forecast_status(
        self,
        request: HttpRequest,
        organization_uuid: str,
        action: Query[Literal["on", "off"]],
        station_uuids: list[str],
    ):
        status = action == "on"
        stations = (
            VirtualStation.objects.for_organization(organization_uuid).active().filter(uuid__in=station_uuids)
        )
        _ = stations.update(
            daily_forecast=status,
            pentad_forecast=status,
            decadal_forecast=status,
            monthly_forecast=status,
            seasonal_forecast=status,
        )
        return 201, stations

    @route.get("", response=list[VirtualStationForecastStatusOutputSchema])
    def get_virtual_stations_forecast_status(self, request: HttpRequest, organization_uuid: str):
        return VirtualStation.objects.for_organization(organization_uuid).active()

    @route.get("{station_uuid}", response=VirtualStationForecastStatusOutputSchema)
    def get_single_virtual_station_forecast_status(
        self, request: HttpRequest, organization_uuid: str, station_uuid: str
    ):
        return VirtualStation.objects.get(uuid=station_uuid, is_deleted=False)

    @route.post("{station_uuid}", response={201: VirtualStationForecastStatusOutputSchema})
    def set_virtual_station_forecast_status(
        self,
        request: HttpRequest,
        organization_uuid: str,
        station_uuid: str,
        forecast_data: VirtualStationForecastStatusInputSchema,
    ):
        station = VirtualStation.objects.get(uuid=station_uuid, is_deleted=False)
        for forecast, value in forecast_data.dict().items():
            setattr(station, forecast, value)

        station.save()

        return 201, station


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

    @route.get("{station_uuid}", response={200: MeteoStationOutputDetailSchema})
    def get_meteorological_station(self, request: HttpRequest, organization_uuid: str, station_uuid: str):
        return MeteorologicalStation.objects.get(uuid=station_uuid, is_deleted=False)

    @route.post("", response={201: MeteoStationOutputDetailSchema})
    def create_meteorological_station(
        self, request: HttpRequest, organization_uuid: str, station_data: MeteoStationInputSchema
    ):
        station_dict = station_data.dict()
        site_uuid = station_dict.pop("site_uuid", None)
        site_data = station_dict.pop("site_data", {})
        if not site_uuid:
            site_data["organization_id"] = organization_uuid
            site = Site.objects.create(**site_data)
            station_dict["site_id"] = site.uuid
        else:
            station_dict["site_id"] = site_uuid

        station = MeteorologicalStation.objects.create(**station_dict)

        return 201, station

    @route.put("{station_uuid}", response={200: MeteoStationOutputDetailSchema, 404: Message})
    def update_station(
        self, request: HttpRequest, organization_uuid: str, station_uuid: str, station_data: MeteoStationUpdateSchema
    ):
        station = MeteorologicalStation.objects.get(uuid=station_uuid, is_deleted=False)
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
        return station

    @route.delete("{station_uuid}", response={200: Message}, permissions=admin_permissions)
    def delete_meteorological_station(self, request: HttpRequest, organization_uuid: str, station_uuid: str):
        station = MeteorologicalStation.objects.get(uuid=station_uuid, is_deleted=False)
        station.is_deleted = True
        station.save()
        return 200, {"detail": _(f"{station.name} station successfully deleted"), "code": "success"}

    @route.get("{station_uuid}/remarks", response={200: list[RemarkOutputSchema]})
    def get_remarks(self, request: HttpRequest, organization_uuid: str, station_uuid: str):
        return Remark.objects.filter(meteo_station=station_uuid)

    @route.post("{station_uuid}/remarks", response={200: RemarkOutputSchema})
    def create_remark(
        self, request: HttpRequest, organization_uuid: str, station_uuid: str, remark_data: RemarkInputSchema
    ):
        remark_dict = remark_data.dict()
        remark_dict["user"] = request.user
        remark_dict["meteo_station_id"] = station_uuid

        remark = Remark.objects.create(**remark_dict)

        return remark

    @route.delete("remarks/{remark_uuid}", response={200: Message})
    def delete_remark(self, request: HttpRequest, organization_uuid: str, remark_uuid: str):
        Remark.objects.filter(uuid=remark_uuid).delete()
        return 200, {"detail": _("Remark deleted successfully"), "code": "success"}


@api_controller(
    "stations/{organization_uuid}/virtual", tags=["Virtual stations"], auth=JWTAuth(), permissions=regular_permissions
)
class VirtualStationsAPIController:
    @route.get("", response=list[VirtualStationListOutputSchema])
    def get_virtual_stations(self, request: HttpRequest, organization_uuid: str):
        return VirtualStation.objects.for_organization(organization_uuid).active()

    @route.get("{virtual_station_uuid}", response={200: VirtualStationDetailOutputSchema})
    def get_virtual_station(self, request: HttpRequest, organization_uuid: str, virtual_station_uuid: str):
        return VirtualStation.objects.get(organization=organization_uuid, uuid=virtual_station_uuid, is_deleted=False)

    @route.post("", response={201: VirtualStationDetailOutputSchema})
    def create_virtual_station(
        self, request: HttpRequest, organization_uuid: str, virtual_station_data: VirtualStationInputSchema
    ):
        payload = virtual_station_data.dict()
        payload["organization_id"] = organization_uuid
        station = VirtualStation.objects.create(**payload)
        return 201, station

    @route.post(
        "{virtual_station_uuid}/associations",
        response={201: VirtualStationDetailOutputSchema},
    )
    def create_virtual_station_associations(
        self,
        request: HttpRequest,
        organization_uuid: str,
        virtual_station_uuid: str,
        association_data: list[VirtualStationAssociationInputSchema],
    ):
        associations = []

        virtual_station = VirtualStation.objects.get(
            organization=organization_uuid, uuid=virtual_station_uuid, is_deleted=False
        )
        for association in association_data:
            hydro_station = HydrologicalStation.objects.get(
                site__organization=organization_uuid, uuid=association.uuid
            )
            association_obj = VirtualStationAssociation(
                virtual_station=virtual_station, hydro_station=hydro_station, weight=association.weight
            )
            associations.append(association_obj)

        # delete all existing associations to set them from scratch
        virtual_station.virtualstationassociation_set.all().delete()
        for obj in associations:
            obj.save()

        return 201, virtual_station

    @route.delete("{virtual_station_uuid}", response={200: Message})
    def delete_virtual_station(self, request: HttpRequest, organization_uuid: str, virtual_station_uuid: str):
        virtual_station = VirtualStation.objects.get(organization=organization_uuid, uuid=virtual_station_uuid)
        virtual_station.is_deleted = True
        virtual_station.save()
        return 200, {"detail": "Station successfully deleted", "code": "deleted"}

    @route.put("{virtual_station_uuid}", response={200: VirtualStationDetailOutputSchema})
    def update_virtual_station(
        self,
        request: HttpRequest,
        organization_uuid: str,
        virtual_station_uuid: str,
        virtual_station_data: VirtualStationUpdateSchema,
    ):
        virtual_station = VirtualStation.objects.get(organization=organization_uuid, uuid=virtual_station_uuid)
        payload = virtual_station_data.dict(exclude_unset=True)

        for attr, value in payload.items():
            setattr(virtual_station, attr, value)

        virtual_station.save()

        return virtual_station
