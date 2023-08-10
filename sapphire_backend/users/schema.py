from django.conf import settings
from django.contrib.auth import get_user_model
from ninja import Field, ModelSchema

from sapphire_backend.organizations.schema import OrganizationOutputDetailSchema
from sapphire_backend.utils.mixins.schemas import UUIDSchemaMixin

User = get_user_model()


class UserInputSchema(ModelSchema):
    class Config:
        model = User
        model_fields = ["username", "email", "user_role"]

    first_name: str | None
    last_name: str | None
    contact_phone: str | None


class UserUpdateSchema(ModelSchema):
    class Config:
        model = User
        model_fields = ["username", "email", "user_role", "first_name", "last_name", "contact_phone"]
        model_fields_optional = "__all__"


class UserOutputSchema(UUIDSchemaMixin, UserInputSchema):
    id: int
    display_name: str = Field(None, alias="display_name")
    avatar: str | None = None
    organization: OrganizationOutputDetailSchema = None

    @staticmethod
    def resolve_avatar(obj: User):
        if not obj.avatar:
            return None

        if obj.avatar.url.startswith("http"):
            return obj.avatar.url
        else:
            return f"{settings.BACKEND_URL}{obj.avatar.url}"
