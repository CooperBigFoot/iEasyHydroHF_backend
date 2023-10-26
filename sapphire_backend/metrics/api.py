from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

# from sapphire_backend.stations.models import Sensor
from sapphire_backend.utils.permissions import IsOrganizationMember, IsSuperAdmin, OrganizationExists


@api_controller(
    "metrics/{organization_uuid}/{station_uuid}",
    tags=["Metrics"],
    auth=JWTAuth(),
    permissions=[OrganizationExists & (IsOrganizationMember | IsSuperAdmin)],
)
class MetricsAPIController:
    @route.get("/latest")
    def get_latest_metrics(self, request, organization_uuid: str, station_uuid: str, sensor_uuid: str = None):
        pass
