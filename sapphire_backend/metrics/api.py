from ninja_extra import api_controller
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.utils.permissions import IsOrganizationMember, IsSuperAdmin, OrganizationExists


@api_controller(
    "metrics/{organization_uuid}/{station_uuid}",
    tags=["Metrics"],
    auth=JWTAuth(),
    permissions=[OrganizationExists & (IsOrganizationMember | IsSuperAdmin)],
)
class MetricsAPIController:
    pass
