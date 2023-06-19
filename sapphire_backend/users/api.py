from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.utils.mixins.schemas import Message

from .schema import UserOutputSchema

User = get_user_model()


@api_controller("users/", tags=["Users"])
class UserAPIController:
    @route.get("me", response=UserOutputSchema, url_name="users-me", auth=JWTAuth())
    def get_current_user(self, request):
        return request.user

    @route.get("{user_id}", response={200: UserOutputSchema, 404: Message}, url_name="user-by-id")
    def get_user_by_id(self, request, user_id: int):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return 404, {"message": _("User not found.")}
