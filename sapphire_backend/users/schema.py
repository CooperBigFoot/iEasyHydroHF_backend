from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from ninja import Field, Schema

from sapphire_backend.organizations.schema import OrganizationOutputListSchema
from sapphire_backend.stations.models import HydrologicalStation, VirtualStation
from sapphire_backend.utils.mixins.schemas import UUIDSchemaMixin

User = get_user_model()


class UserInputSchema(Schema):
    username: str
    email: str
    user_role: User.UserRoles
    language: User.Language
    is_active: bool | None = True
    first_name: str | None = ""
    last_name: str | None = ""
    contact_phone: str | None = ""


class UserUpdateSchema(UserInputSchema):
    username: str | None = None
    email: str | None = None
    user_role: User.UserRoles | None = None
    language: User.Language | None = None
    is_active: bool | None = None


class UserAvatarSchema(Schema):
    avatar: str | None = None

    @staticmethod
    def resolve_avatar(obj: User):
        if not obj.avatar:
            return None

        if obj.avatar.url.startswith("http"):
            return obj.avatar.url
        else:
            return f"{settings.BACKEND_URL}{obj.avatar.url}"


class UserAssignedStationOutputSchema(Schema):
    id: int = Field(..., alias="station.id")
    name: str = Field(..., alias="station.name")
    station_code: str = Field(..., alias="station.station_code")
    uuid: str
    station_type: str | None
    created_date: datetime

    @staticmethod
    def resolve_uuid(obj):
        return str(obj.station.uuid)

    @staticmethod
    def resolve_station_type(obj):
        if isinstance(obj.station, HydrologicalStation):
            return obj.station.station_type
        elif isinstance(obj.station, VirtualStation):
            return "V"
        else:
            return None


class UserOutputListSchema(UserInputSchema, UserAvatarSchema, UUIDSchemaMixin):
    display_name: str = Field(None, alias="display_name")


class UserOutputDetailSchema(UserOutputListSchema):
    id: int
    organization: OrganizationOutputListSchema | None = None


class UserAssignedStationInputSchema(Schema):
    hydro_station_id: str | None = None
    meteo_station_id: str | None = None
    virtual_station_id: str | None = None


class ChangePasswordSchema(Schema):
    old_password: str
    new_password: str
    confirm_new_password: str
