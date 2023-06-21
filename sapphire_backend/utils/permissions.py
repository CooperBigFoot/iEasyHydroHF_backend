from django.contrib.auth import get_user_model
from django.http import HttpRequest
from ninja_extra import permissions
from ninja_extra.controllers import ControllerBase

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
            # TODO find out how to get the organization ID, most likely from the controller path or something
            return (
                user.user_role == User.UserRoles.ORGANIZATION_ADMIN and user.organization.id == "some_organization_id"
            )
        return False
