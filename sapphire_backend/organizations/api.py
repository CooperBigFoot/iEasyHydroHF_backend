from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils.translation import gettext as _
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.users.schema import UserInputSchema, UserOutputDetailSchema, UserOutputListSchema
from sapphire_backend.utils.mixins.schemas import FieldMessage, Message
from sapphire_backend.utils.permissions import (
    IsOrganizationAdmin,
    IsOrganizationMember,
    IsSuperAdmin,
    OrganizationExists,
)

from .models import Basin, Organization, Region
from .schema import (
    BasinInputSchema,
    BasinOutputSchema,
    OrganizationInputSchema,
    OrganizationOutputDetailSchema,
    OrganizationOutputListSchema,
    OrganizationUpdateSchema,
    RegionInputSchema,
    RegionOutputSchema,
)

User = get_user_model()


@api_controller(
    "basins/{organization_uuid}",
    tags=["Basins"],
    auth=JWTAuth(),
    permissions=[OrganizationExists],
)
class BasinsAPIController:
    @route.post("", response={201: BasinOutputSchema})
    def create_basin(self, request, organization_uuid: str, basin_data: BasinInputSchema):
        organization = Organization.objects.get(uuid=organization_uuid)
        basin_dict = basin_data.dict()
        basin_dict["organization"] = organization
        basin = Basin.objects.create(**basin_dict)

        return 201, basin

    @route.get("{basin_uuid}", response={200: BasinOutputSchema, 404: Message})
    def get_basin(self, request, organization_uuid: str, basin_uuid: str):
        try:
            return 200, Basin.objects.get(uuid=basin_uuid)
        except Basin.DoesNotExist:
            return 404, {"detail": _("Basin not found."), "code": "not_found"}

    @route.get("", response={200: list[BasinOutputSchema]})
    def get_organization_basins(self, request, organization_uuid: str):
        return Basin.objects.filter(organization=organization_uuid)

    @route.put("{basin_uuid}", response={200: BasinOutputSchema, 404: Message})
    def update_basin(self, request, organization_uuid: str, basin_uuid: str, basin_data: BasinInputSchema):
        try:
            basin = Basin.objects.get(uuid=basin_uuid)
            for attr, value in basin_data.dict(exclude_unset=True).items():
                setattr(basin, attr, value)
            basin.save()
            return 200, basin
        except IntegrityError:
            return 404, {"detail": _("Basin not found."), "code": "not_found"}

    @route.delete("{basin_uuid}", response={200: Message, 400: Message})
    def delete_basin(self, request, organization_uuid: str, basin_uuid: str):
        try:
            Basin.objects.filter(uuid=basin_uuid).delete()
            return 200, {"detail": _("Basin deleted successfully"), "code": "success"}
        except IntegrityError:
            return 400, {"detail": _("Basin could not be deleted"), "code": "error"}


@api_controller(
    "regions/{organization_uuid}",
    tags=["Regions"],
    auth=JWTAuth(),
    permissions=[OrganizationExists],
)
class RegionsAPIController:
    @route.post("", response={201: RegionOutputSchema})
    def create_region(self, request, organization_uuid: str, region_data: RegionInputSchema):
        organization = Organization.objects.get(uuid=organization_uuid)
        region_dict = region_data.dict()
        region_dict["organization"] = organization
        region = Region.objects.create(**region_dict)

        return 201, region

    @route.get("{region_uuid}", response={200: RegionOutputSchema, 404: Message})
    def get_basin(self, request, organization_uuid: str, region_uuid: str):
        try:
            return 200, Region.objects.get(uuid=region_uuid)
        except Region.DoesNotExist:
            return 404, {"detail": _("Region not found."), "code": "not_found"}

    @route.get("", response={200: list[RegionOutputSchema]})
    def get_organization_regions(self, request, organization_uuid: str):
        return Region.objects.filter(organization=organization_uuid)

    @route.put("{region_uuid}", response={200: RegionOutputSchema, 404: Message})
    def update_region(self, request, organization_uuid: str, region_uuid: str, region_data: RegionInputSchema):
        try:
            region = Region.objects.get(uuid=region_uuid)
            for attr, value in region_data.dict(exclude_unset=True).items():
                setattr(region, attr, value)
            region.save()
            return 200, region
        except IntegrityError:
            return 404, {"detail": _("Region not found."), "code": "not_found"}

    @route.delete("{region_uuid}", response={200: Message, 400: Message})
    def delete_region(self, request, organization_uuid: str, region_uuid: str):
        try:
            Region.objects.filter(uuid=region_uuid).delete()
            return 200, {"detail": _("Region deleted successfully"), "code": "success"}
        except IntegrityError:
            return 400, {"detail": _("Region could not be deleted"), "code": "error"}


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
        permissions=[OrganizationExists & (IsSuperAdmin | IsOrganizationAdmin | IsOrganizationMember)],
    )
    def get_organization(self, request, organization_uuid: str):
        return Organization.objects.get(uuid=organization_uuid)

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
        url_name="get-organization-members",
    )
    def organization_members(self, request, organization_uuid: str):
        organization = Organization.objects.get(uuid=organization_uuid)
        return organization.members.filter(is_deleted=False)

    @route.post(
        "{organization_uuid}/members/add",
        response={200: UserOutputDetailSchema, 400: FieldMessage},
        permissions=[OrganizationExists & (IsOrganizationAdmin | IsSuperAdmin)],
        url_name="add-organization-member",
    )
    def add_organization_member(self, request, organization_uuid: str, user_payload: UserInputSchema):
        organization = Organization.objects.get(uuid=organization_uuid)
        user_dict = user_payload.dict()
        user_dict["organization"] = organization
        try:
            user = User.objects.create(**user_dict)
        except IntegrityError:
            return 400, {"message": _("Username already taken"), "field": "username"}

        return user
