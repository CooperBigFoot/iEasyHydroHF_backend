from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from ninja import File
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.utils.mixins.files import UploadedLimitedSizeFile
from sapphire_backend.utils.mixins.schemas import Message
from sapphire_backend.utils.permissions import IsOwner, IsSuperAdmin

from .schema import UserOutputDetailSchema, UserUpdateSchema
from .utils import can_update_role

User = get_user_model()


@api_controller("users/", tags=["Users"], auth=JWTAuth())
class UsersAPIController:
    @route.get("me", response=UserOutputDetailSchema, url_name="users-me")
    def get_current_user(self, request):
        return request.user

    @route.get("{user_id}", response={200: UserOutputDetailSchema, 404: Message}, url_name="user-by-id")
    def get_user_by_id(self, request, user_id: int):
        try:
            return User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return 404, {"detail": _("User not found."), "code": "user_not_found"}

    @route.post("me/avatar-upload", response={201: UserOutputDetailSchema}, url_name="users-me-avatar-upload")
    def upload_avatar(self, request, image: UploadedLimitedSizeFile = File(...)):
        request.user.avatar.save(image.name, image.file)
        request.user.save()
        return 201, request.user

    @route.put(
        "{user_id}",
        response={200: UserOutputDetailSchema, 403: Message, 404: Message},
        url_name="user-update",
        permissions=[IsOwner | IsSuperAdmin],
    )
    def update_user(self, request, user_id: int, user_data: UserUpdateSchema):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return 404, {"detail": "User not found", "code": "user_not_found"}
        for attr, value in user_data.dict(exclude_unset=True).items():
            if attr == "user_role" and not can_update_role(request.user, value):
                return 403, {
                    "detail": "Role cannot be changed, please contact your administrator.",
                    "code": "role_change_error",
                }
            setattr(user, attr, value)
        user.save()
        return user
