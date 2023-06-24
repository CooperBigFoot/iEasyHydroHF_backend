from django.contrib.auth import get_user_model
from django.http import HttpRequest
from ninja_extra import permissions
from ninja_extra.controllers import ControllerBase

from sapphire_backend.organizations.models import Organization

User = get_user_model()


class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request: HttpRequest, controller: "ControllerBase") -> bool:
        if request.user.is_authenticated:
            return request.user.user_role == User.UserRoles.SUPER_ADMIN
        return False


class IsOrganizationAdmin(permissions.BasePermission):
    def has_permission(self, request: HttpRequest, controller: "ControllerBase") -> bool:
        user = request.user
        if user.is_authenticated:
            return (
                user.user_role == User.UserRoles.ORGANIZATION_ADMIN
                and user.organization.id == controller.context.kwargs.get("organization_id")
            )
        return False


class OgranizationExists(permissions.BasePermission):
    def has_permission(self, request: HttpRequest, controller: "ControllerBase") -> bool:
        return Organization.objects.filter(id=controller.context.kwargs.get("organization_id")).exists()
