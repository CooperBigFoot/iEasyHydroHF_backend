from django.contrib.auth import get_user_model

User = get_user_model()


def can_update_role(user: User, new_role: str):
    if user.is_organization_admin and new_role == User.UserRoles.ORGANIZATION_ADMIN:
        return True
    elif user.is_superadmin:
        return True
    return False
