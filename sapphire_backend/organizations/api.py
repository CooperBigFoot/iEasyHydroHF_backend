from django.db import IntegrityError
from django.utils.translation import gettext as _
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.users.schema import UserOutputListSchema
from sapphire_backend.utils.mixins.schemas import Message
from sapphire_backend.utils.permissions import (
    IsOrganizationAdmin,
    IsOrganizationMember,
    IsSuperAdmin,
    OrganizationExists,
)

from .models import Organization
from .schema import (
    OrganizationInputSchema,
    OrganizationOutputDetailSchema,
    OrganizationOutputListSchema,
    OrganizationUpdateSchema,
)


@api_controller("organizations", tags=["Organizations"], auth=JWTAuth())
class OrganizationsAPIController:
    @route.post("", response={201: OrganizationOutputDetailSchema, 401: Message}, permissions=[IsSuperAdmin])
    def create_organization(self, request, organization_data: OrganizationInputSchema):
        organization = Organization.objects.create(**organization_data.dict())

        return 201, organization

    @route.get("", response=list[OrganizationOutputListSchema], permissions=[IsSuperAdmin])
    def get_organizations(self, request):
        return Organization.objects.all()

    @route.get(
        "{organization_uuid}",
        response=OrganizationOutputDetailSchema,
        permissions=[OrganizationExists & (IsSuperAdmin | IsOrganizationAdmin)],
    )
    def get_organization(self, request, organization_uuid: str):
        Organization.objects.get(uuid=organization_uuid)

    @route.delete(
        "{organization_uuid}",
        response=Message,
        permissions=[OrganizationExists & (IsSuperAdmin | IsOrganizationAdmin)],
    )
    def delete_organization(self, request, organization_uuid: str):
        try:
            organization = Organization.objects.get(uuid=organization_uuid)
            organization.delete()
            return 200, {"detail": "Organization successfully deleted", "code": "success"}
        except IntegrityError:
            return 400, {"detail": _("Organization could not be deleted."), "code": "error"}

    @route.put(
        "{organization_uuid}",
        response=OrganizationOutputDetailSchema,
        permissions=[OrganizationExists & (IsSuperAdmin | IsOrganizationAdmin)],
    )
    def update_organization(self, request, organization_uuid: str, organization_data: OrganizationUpdateSchema):
        organization = Organization.objects.get(uuid=organization_uuid)
        for attr, value in organization_data.dict(exclude_unset=True).items():
            setattr(organization, attr, value)
        organization.save()
        return 200, organization

    @route.get(
        "{organization_uuid}/members",
        response=list[UserOutputListSchema],
        permissions=[OrganizationExists & (IsOrganizationAdmin | IsOrganizationMember | IsSuperAdmin)],
    )
    def organization_members(self, request, organization_uuid: str):
        organization = Organization.objects.get(uuid=organization_uuid)
        return organization.members
