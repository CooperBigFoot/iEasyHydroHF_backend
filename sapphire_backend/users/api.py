from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from ninja import File
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.utils.mixins.files import UploadedLimitedSizeFile
from sapphire_backend.utils.mixins.schemas import Message

from .schema import UserOutputSchema

User = get_user_model()


@api_controller("users/", tags=["Users"])
class UsersAPIController:
    @route.get("me", response=UserOutputSchema, url_name="users-me", auth=JWTAuth())
    def get_current_user(self, request):
        return request.user

    @route.get("{user_id}", response={200: UserOutputSchema, 404: Message}, url_name="user-by-id")
    def get_user_by_id(self, request, user_id: int):
        try:
            return User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return 404, {"detail": _("User not found."), "code": "user_not_found"}

    @route.post(
        "me/avatar-upload", response={201: UserOutputSchema}, url_name="users-me-avatar-upload", auth=JWTAuth()
    )
    def upload_avatar(self, request, image: UploadedLimitedSizeFile = File(...)):
        request.user.avatar.save(image.name, image.file)
        request.user.save()
        return 201, request.user
