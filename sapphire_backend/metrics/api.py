from django.utils.translation import gettext_lazy as _
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.stations.models import Sensor
from sapphire_backend.utils.permissions import (
    IsOrganizationMember,
    IsSuperAdmin,
    OrganizationExists,
    StationBelongsToOrganization,
)


@api_controller(
    "metrics/{organization_uuid}/{station_uuid}",
    tags=["Metrics"],
    auth=JWTAuth(),
    permissions=[OrganizationExists & (IsOrganizationMember | IsSuperAdmin) & StationBelongsToOrganization],
)
class MetricsAPIController:
    @route.get("/latest")
    def get_latest_metrics(self, request, organization_uuid: str, station_uuid: str, sensor_uuid: str = None):
        try:
            if sensor_uuid:
                sensor = Sensor.objects.for_station(station_uuid).get(uuid=sensor_uuid, is_active=True)
            else:
                sensor = Sensor.objects.for_station(station_uuid).get(is_default=True)
        except Sensor.DoesNotExist:
            return 404, {
                "detail": _("Station or sensor does not exist"),
                "code": "not_found",
            }
        print(sensor)

    @route.get("/timeseries")
    def get_timeseries(self, request, organization_uuid: str, station_uuid: str, sensor_uuid: str = None):
        pass
