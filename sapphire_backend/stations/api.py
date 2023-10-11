from django.db import IntegrityError
from django.utils.translation import gettext as _
from ninja import Query
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.utils.mixins.schemas import Message
from sapphire_backend.utils.permissions import IsOrganizationAdmin, IsSuperAdmin, OrganizationExists

from .models import Station
from .schema import StationFilterSchema, StationInputSchema, StationOutputDetailSchema, StationUpdateSchema


@api_controller(
    "{organization_uuid}/stations",
    tags=["Stations"],
    auth=JWTAuth(),
    permissions=[OrganizationExists & (IsOrganizationAdmin | IsSuperAdmin)],
)
class StationsAPIController:
    @route.post("", response={201: StationOutputDetailSchema, 400: Message})
    def create_station(self, request, organization_uuid: str, station_data: StationInputSchema):
        try:
            station = Station.objects.create(**station_data.dict())
        except IntegrityError:
            return 400, {"detail": _("Station with the same code already exists."), "code": "duplicate_station"}

        return 201, station

    @route.get("", response=list[StationOutputDetailSchema])
    def get_stations(self, request, organization_uuid: str, station_type_filter: StationFilterSchema = Query(...)):
        stations = Station.objects.filter(organization__uuid=organization_uuid)
        if station_type_filter.station_type:
            stations = stations.filter(station_type=station_type_filter.station_type.value)

        return stations

    @route.get("{station_id}", response={200: StationOutputDetailSchema, 404: Message})
    def get_station(self, request, organization_uuid: str, station_id: int):
        try:
            return 200, Station.objects.get(id=station_id)
        except Station.DoesNotExist:
            return 404, {"detail": _("Station not found."), "code": "not_found"}

    @route.delete("{station_id}", response=Message)
    def delete_station(self, request, organization_uuid: str, station_id: int):
        try:
            station = Station.objects.get(id=station_id)
            station.delete()
            return 200, {"detail": "Station successfully deleted", "code": "success"}
        except Station.DoesNotExist:
            return 404, {"detail": _("Station not found."), "code": "not_found"}
        except IntegrityError:
            return 400, {"detail": _("Station could not be deleted."), "code": "error"}

    @route.put("{station_id}", response={200: StationOutputDetailSchema, 404: Message})
    def update_station(self, request, organization_uuid: str, station_id: int, station_data: StationUpdateSchema):
        try:
            station = Station.objects.get(id=station_id)
            for attr, value in station_data.dict(exclude_unset=True).items():
                setattr(station, attr, value)
            station.save()
            return 200, station
        except Station.DoesNotExist:
            return 404, {"detail": _("Station not found."), "code": "not_found"}
