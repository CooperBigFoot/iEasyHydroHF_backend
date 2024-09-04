from django.contrib.auth import get_user_model
from django.http import HttpRequest
from ninja_extra import permissions
from ninja_extra.controllers import ControllerBase

from sapphire_backend.estimations.models import DischargeModel
from sapphire_backend.organizations.models import Organization
from sapphire_backend.stations.models import HydrologicalStation, MeteorologicalStation

User = get_user_model()


def get_user_from_kwargs(kwargs):
    user = None
    if (user_id := kwargs.get("user_id")) is not None:
        user = User.objects.filter(id=user_id).first()
    elif (user_uuid := kwargs.get("user_uuid")) is not None:
        user = User.objects.filter(uuid=user_uuid).first()
    return user


def get_station_from_kwargs(kwargs):
    station = None
    if (discharge_model_id := kwargs.get("discharge_model_id")) is not None:
        model_obj = DischargeModel.objects.filter(id=discharge_model_id).first()
        station = getattr(model_obj, "station", None)
    if (discharge_model_uuid := kwargs.get("discharge_model_uuid")) is not None:
        model_obj = DischargeModel.objects.filter(uuid=discharge_model_uuid).first()
        station = getattr(model_obj, "station", None)
    elif (station_id := kwargs.get("station_id")) is not None:
        station = (
            HydrologicalStation.objects.filter(id=station_id).first()
            or MeteorologicalStation.objects.filter(id=station_id).first()
        )
    elif (station_uuid := kwargs.get("station_uuid")) is not None:
        station = (
            HydrologicalStation.objects.filter(uuid=station_uuid).first()
            or MeteorologicalStation.objects.filter(uuid=station_uuid).first()
        )
    return station


def get_organization_from_kwargs(kwargs):
    organization_obj = None
    if (organization_id := kwargs.get("organization_id")) is not None:
        organization_obj = Organization.objects.filter(id=organization_id).first()
    elif (organization_uuid := kwargs.get("organization_uuid")) is not None:
        organization_obj = Organization.objects.filter(uuid=organization_uuid).first()
    else:
        if (station := get_station_from_kwargs(kwargs)) is not None:
            organization_obj = station.site.organization
        elif (user := get_user_from_kwargs(kwargs)) is not None:
            organization_obj = user.organization
    return organization_obj


class IsOwner(permissions.BasePermission):
    def has_permission(self, request: HttpRequest, controller: "ControllerBase") -> bool:
        return request.user.is_authenticated and (str(request.user.uuid) == controller.context.kwargs.get("user_uuid"))


class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request: HttpRequest, controller: "ControllerBase") -> bool:
        return request.user.is_authenticated and (request.user.user_role == User.UserRoles.SUPER_ADMIN)


class IsOrganizationAdmin(permissions.BasePermission):
    def has_permission(self, request: HttpRequest, controller: "ControllerBase") -> bool:
        user = request.user
        organization = get_organization_from_kwargs(controller.context.kwargs)
        if user.is_authenticated:
            return user.organization.id == organization.id and user.user_role == User.UserRoles.ORGANIZATION_ADMIN
        return False


class IsInTheSameOrganization(permissions.BasePermission):
    def has_permission(self, request: HttpRequest, controller: "ControllerBase") -> bool:
        user = request.user
        if user.is_authenticated:
            second_user = get_user_from_kwargs(controller.context.kwargs)
            if second_user:
                return user.organization == second_user.organization

        return False


class IsOrganizationMember(permissions.BasePermission):
    def has_permission(self, request: HttpRequest, controller: "ControllerBase") -> bool:
        user = request.user
        organization = get_organization_from_kwargs(controller.context.kwargs)
        if user.is_authenticated:
            return user.organization.id == organization.id
        return False


class OrganizationExists(permissions.BasePermission):
    def has_permission(self, request: HttpRequest, controller: "ControllerBase") -> bool:
        return get_organization_from_kwargs(controller.context.kwargs) is not None


class StationExists(permissions.BasePermission):
    def has_permission(self, request: HttpRequest, controller: "ControllerBase") -> bool:
        station = get_station_from_kwargs(controller.context.kwargs)
        return station is not None


class HydroStationBelongsToOrganization(permissions.BasePermission):
    def has_permission(self, request: HttpRequest, controller: "ControllerBase") -> bool:
        return HydrologicalStation.objects.filter(
            site__organization=controller.context.kwargs.get("organization_uuid"),
            uuid=controller.context.kwargs.get("station_uuid"),
        ).exists()


regular_permissions = [OrganizationExists & (IsOrganizationMember | IsSuperAdmin)]
admin_permissions = [OrganizationExists & (IsOrganizationAdmin | IsSuperAdmin)]
