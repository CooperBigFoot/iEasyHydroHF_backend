from django.conf import settings
from django.contrib.auth import get_user_model
from ninja import Field, ModelSchema

from sapphire_backend.organizations.schema import OrganizationOutputListSchema
from sapphire_backend.utils.mixins.schemas import UUIDSchemaMixin

User = get_user_model()


class UserInputSchema(ModelSchema):
    class Meta:
        model = User
        fields = ["username", "email", "user_role", "language", "is_active"]

    first_name: str | None
    last_name: str | None
    contact_phone: str | None


class UserUpdateSchema(ModelSchema):
    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "user_role",
            "first_name",
            "last_name",
            "contact_phone",
            "language",
            "is_active",
        ]
        model_fields_optional = "__all__"


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
