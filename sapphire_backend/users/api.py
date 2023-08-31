import uuid

from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from ninja import File
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.utils.mixins.files import UploadedLimitedSizeFile
from sapphire_backend.utils.mixins.schemas import Message
from sapphire_backend.utils.permissions import IsOrganizationAdmin, IsOwner, IsSuperAdmin

from .schema import UserOutputDetailSchema, UserUpdateSchema
from .utils import can_update_role

User = get_user_model()


@api_controller("users/", tags=["Users"], auth=JWTAuth())
class UsersAPIController:
    @route.get("me", response=UserOutputDetailSchema, url_name="users-me")
    def get_current_user(self, request):
        return request.user

    @route.get("{user_uuid}", response={200: UserOutputDetailSchema, 404: Message}, url_name="user-by-uuid")
    def get_user_by_id(self, request, user_uuid: str):
        try:
            return User.objects.get(uuid=user_uuid)
        except User.DoesNotExist:
            return 404, {"detail": _("User not found."), "code": "user_not_found"}

    @route.post("me/avatar-upload", response={201: UserOutputDetailSchema}, url_name="users-me-avatar-upload")
    def upload_avatar(self, request, image: UploadedLimitedSizeFile = File(...)):
        request.user.avatar.save(image.name, image.file)
        request.user.save()
        return 201, request.user

    @route.put(
        "{user_uuid}",
        response={200: UserOutputDetailSchema, 403: Message, 404: Message},
        url_name="user-update",
        permissions=[IsOwner | IsSuperAdmin],
    )
    def update_user(self, request, user_uuid: str, user_data: UserUpdateSchema):
        try:
            user = User.objects.get(uuid=user_uuid)
        except User.DoesNotExist:
            return 404, {"detail": "User not found", "code": "user_not_found"}
        for attr, value in user_data.dict(exclude_unset=True).items():
            if attr == "user_role" and not can_update_role(request.user, value):
                return 403, {
                    "detail": _("Role cannot be changed, please contact your administrator."),
                    "code": "role_change_error",
                }
            setattr(user, attr, value)
        user.save()
        return user

    @route.delete(
        "{user_uuid}",
        response={200: Message, 403: Message, 404: Message},
        url_name="user-delete",
        permissions=[IsSuperAdmin | IsOrganizationAdmin],
    )
    def delete_user(self, request, user_uuid: str):
        try:
            user = User.objects.get(uuid=user_uuid)
        except User.DoesNotExist:
            return 404, {"detail": _("User not found"), "code": "user_not_found"}

        if user == request.user:
            return 403, {
                "detail": _("Cannot delete yourself. Please use the account deactivation feature."),
                "code": "delete_error",
            }
        user.delete()

        return 200, {"detail": _("User successfully deleted"), "code": "delete_success"}

    @route.delete(
        "bulk-delete/{user_uuids}",
        response={200: Message, 400: Message, 403: Message},
        url_name="bulk-user-delete",
        permissions=[IsSuperAdmin | IsOrganizationAdmin],
    )
    def bulk_delete_user(self, request, user_uuids: list[str]):
        try:
            for user_uuid in user_uuids:
                uuid.UUID(user_uuid)
        except ValueError:
            return 400, {"detail": _(f"{user_uuid} is not a valid UUID."), "code": "invalid_uuid"}

        if str(request.user.uuid) in user_uuids:
            return 403, {
                "detail": _("Cannot delete yourself. Please use the account deactivation feature."),
                "code": "delete_error",
            }

        User.objects.filter(uuid__in=user_uuids).delete()

        return 200, {"detail": _("Users successfully deleted"), "code": "delete_success"}
