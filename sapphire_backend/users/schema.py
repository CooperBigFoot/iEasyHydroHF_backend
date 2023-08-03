from django.conf import settings
from django.contrib.auth import get_user_model
from ninja import Field, ModelSchema

User = get_user_model()


class UserOutputSchema(ModelSchema):
    class Config:
        model = User
        model_fields = ["id", "username", "email", "first_name", "last_name", "contact_phone", "user_role"]

    display_name: str = Field(None, alias="display_name")
    avatar: str | None = None

    @staticmethod
    def resolve_avatar(obj: User):
        if not obj.avatar:
            return None

        if obj.avatar.url.startswith("http"):
            return obj.avatar.url
        else:
            return f"{settings.BACKEND_URL}{obj.avatar.url}"
