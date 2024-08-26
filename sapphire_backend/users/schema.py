from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from ninja import Field, Schema

from sapphire_backend.organizations.schema import OrganizationOutputListSchema
from sapphire_backend.stations.schema import (
    HydrologicalStationNestedSchema,
    MeteoStationNestedSchema,
    VirtualStationNestedSchema,
)
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


class UserOutputListSchema(UserInputSchema, UserAvatarSchema, UUIDSchemaMixin):
    display_name: str = Field(None, alias="display_name")


class UserOutputNestedSchema(UserAvatarSchema, UUIDSchemaMixin, Schema):
    display_name: str = Field(None, alias="display_name")
    username: str
    email: str
    id: int


class UserOutputDetailSchema(UserOutputListSchema):
    id: int
    organization: OrganizationOutputListSchema | None = None


class UserAssignedStationInputSchema(Schema):
    hydro_station_id: str | None = None
    meteo_station_id: str | None = None
    virtual_station_id: str | None = None


class UserAssignedStationOutputSchema(Schema):
    assigned_by: UserOutputNestedSchema
    hydro_station: HydrologicalStationNestedSchema | None = None
    meteo_station: MeteoStationNestedSchema | None = None
    virtual_station: VirtualStationNestedSchema | None = None
    created_date: datetime
