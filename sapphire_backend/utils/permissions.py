from django.contrib.auth import get_user_model
from django.http import HttpRequest
from ninja_extra import permissions
from ninja_extra.controllers import ControllerBase

from sapphire_backend.estimations.models import DischargeModel
from sapphire_backend.organizations.models import Organization
from sapphire_backend.stations.models import HydrologicalStation, MeteorologicalStation

User = get_user_model()


def get_station_from_kwargs(kwargs):
    station = None
    if kwargs.get("discharge_model_id") is not None:
        model_obj = DischargeModel.objects.filter(id=kwargs.get("discharge_model_id")).first()
        station = model_obj.station
    elif kwargs.get("station_id") is not None:
        station = (
            HydrologicalStation.objects.filter(id=kwargs.get("station_id")).first()
            or MeteorologicalStation.objects.filter(id=kwargs.get("station_id")).first()
        )
    elif kwargs.get("station_uuid") is not None:
        station = (
            HydrologicalStation.objects.filter(uuid=kwargs.get("station_uuid")).first()
            or MeteorologicalStation.objects.filter(uuid=kwargs.get("station_uuid")).first()
        )
    return station


def get_organization_from_kwargs(kwargs):
    organization_obj = None
    if kwargs.get("organization_id") is not None:
        organization_obj = Organization.objects.filter(id=kwargs.get("organization_id")).first()
    elif kwargs.get("organization_uuid") is not None:
        organization_obj = Organization.objects.filter(uuid=kwargs.get("organization_uuid")).first()
    else:
        station = get_station_from_kwargs(kwargs)
        if station is not None:
            organization_obj = station.site.organization
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
        # organization = Organization.objects.get(uuid=controller.context.kwargs.get("organization_uuid"))
        organization = get_organization_from_kwargs(controller.context.kwargs)
        if user.is_authenticated:
            return user.organization.id == organization.id and user.user_role == User.UserRoles.ORGANIZATION_ADMIN
        return False


class IsOrganizationMember(permissions.BasePermission):
    def has_permission(self, request: HttpRequest, controller: "ControllerBase") -> bool:
        user = request.user
        # organization = Organization.objects.get(uuid=controller.context.kwargs.get("organization_uuid"))
        organization = get_organization_from_kwargs(controller.context.kwargs)
        if user.is_authenticated:
            return user.organization.id == organization.id
        return False


class OrganizationExists(permissions.BasePermission):
    def has_permission(self, request: HttpRequest, controller: "ControllerBase") -> bool:
        # return Organization.objects.filter(uuid=controller.context.kwargs.get("organization_uuid")).exists()
        return get_organization_from_kwargs(controller.context.kwargs) is not None


class StationExists(permissions.BasePermission):
    def has_permission(self, request: HttpRequest, controller: "ControllerBase") -> bool:
        hydro_station = get_station_from_kwargs(controller.context.kwargs)
        return hydro_station is not None


class HydroStationBelongsToOrganization(permissions.BasePermission):
    def has_permission(self, request: HttpRequest, controller: "ControllerBase") -> bool:
        return HydrologicalStation.objects.filter(
            site__organization=controller.context.kwargs.get("organization_uuid"),
            uuid=controller.context.kwargs.get("station_uuid"),
        ).exists()


regular_permissions = [OrganizationExists & (IsOrganizationMember | IsSuperAdmin)]
admin_permissions = [OrganizationExists & (IsOrganizationAdmin | IsSuperAdmin)]
