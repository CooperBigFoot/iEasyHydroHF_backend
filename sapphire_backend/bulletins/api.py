from ninja import Query
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.utils.permissions import (
    regular_permissions,
)

from .models import BulletinTemplate
from .schema import BulletinOutputSchema, BulletinTypeFilterSchema


@api_controller("bulletins/{organization_uuid}", tags=["Bulletins"], auth=JWTAuth(), permissions=regular_permissions)
class BulletinsAPIController:
    @route.get("", response={200: list[BulletinOutputSchema]})
    def get_organization_bulletins(self, organization_uuid: str, filters: Query[BulletinTypeFilterSchema]):
        filters_dict = filters.dict(exclude_none=True)
        return BulletinTemplate.objects.for_organization(organization_uuid).filter(**filters_dict)
