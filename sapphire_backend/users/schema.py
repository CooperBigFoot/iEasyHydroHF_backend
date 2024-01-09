from django.conf import settings
from django.contrib.auth import get_user_model
from ninja import Field, Schema

from sapphire_backend.organizations.schema import OrganizationOutputListSchema
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


class UserOutputListSchema(UserInputSchema, UUIDSchemaMixin):
    avatar: str | None = None
    display_name: str = Field(None, alias="display_name")

    @staticmethod
    def resolve_avatar(obj: User):
        if not obj.avatar:
            return None

        if obj.avatar.url.startswith("http"):
            return obj.avatar.url
        else:
            return f"{settings.BACKEND_URL}{obj.avatar.url}"


class UserOutputDetailSchema(UserOutputListSchema):
    id: int
    organization: OrganizationOutputListSchema | None = None
