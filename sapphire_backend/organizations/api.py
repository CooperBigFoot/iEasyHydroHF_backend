from django.db import IntegrityError
from django.utils.translation import gettext as _
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.utils.mixins.schemas import Message
from sapphire_backend.utils.permissions import IsOrganizationAdmin, IsSuperAdmin

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
        "{organization_id}",
        response={200: OrganizationOutputDetailSchema, 404: Message},
        permissions=[IsSuperAdmin | IsOrganizationAdmin],
    )
    def get_organization(self, request, organization_id: int):
        try:
            return 200, Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            return 404, {"detail": _("Organization not found."), "code": "not_found"}

    @route.delete("{organization_id}", response=Message, permissions=[IsSuperAdmin])
    def delete_organization(self, request, organization_id: int):
        try:
            organization = Organization.objects.get(id=organization_id)
            organization.delete()
            return 200, {"detail": "Organization successfully deleted", "code": "success"}
        except Organization.DoesNotExist:
            return 404, {"detail": _("Organization not found."), "code": "not_found"}
        except IntegrityError:
            return 400, {"detail": _("Organization could not be deleted."), "code": "error"}

    @route.put("{organization_id}", response={200: OrganizationOutputDetailSchema, 404: Message})
    def update_organization(self, request, organization_id: int, organization_data: OrganizationUpdateSchema):
        try:
            organization = Organization.objects.get(id=organization_id)
            for attr, value in organization_data.dict(exclude_unset=True).items():
                setattr(organization, attr, value)
            organization.save()
            return 200, organization
        except Organization.DoesNotExist:
            return 404, {"detail": _("Organization not found."), "code": "not_found"}
