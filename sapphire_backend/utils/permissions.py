from django.contrib.auth import get_user_model
from django.http import HttpRequest
from ninja_extra import permissions
from ninja_extra.controllers import ControllerBase

from sapphire_backend.organizations.models import Organization
from sapphire_backend.stations.models import HydrologicalStation

User = get_user_model()


class IsOwner(permissions.BasePermission):
    def has_permission(self, request: HttpRequest, controller: "ControllerBase") -> bool:
        return request.user.is_authenticated and (str(request.user.uuid) == controller.context.kwargs.get("user_uuid"))


class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request: HttpRequest, controller: "ControllerBase") -> bool:
        return request.user.is_authenticated and (request.user.user_role == User.UserRoles.SUPER_ADMIN)


class IsOrganizationAdmin(permissions.BasePermission):
    def has_permission(self, request: HttpRequest, controller: "ControllerBase") -> bool:
        return request.user.is_authenticated and (request.user.user_role == User.UserRoles.ORGANIZATION_ADMIN)


class IsOrganizationMember(permissions.BasePermission):
    def has_permission(self, request: HttpRequest, controller: "ControllerBase") -> bool:
        user = request.user
        organization = Organization.objects.get(uuid=controller.context.kwargs.get("organization_uuid"))
        if user.is_authenticated:
            return user.organization.id == organization.id
        return False


class OrganizationExists(permissions.BasePermission):
    def has_permission(self, request: HttpRequest, controller: "ControllerBase") -> bool:
        return Organization.objects.filter(uuid=controller.context.kwargs.get("organization_uuid")).exists()


class HydroStationBelongsToOrganization(permissions.BasePermission):
    def has_permission(self, request: HttpRequest, controller: "ControllerBase") -> bool:
        return HydrologicalStation.objects.filter(
            site__organization=controller.context.kwargs.get("organization_uuid"),
            uuid=controller.context.kwargs.get("station_uuid"),
        ).exists()
