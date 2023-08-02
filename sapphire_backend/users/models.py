from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    class UserRoles(models.TextChoices):
        REGULAR_USER = "regular_user", _("Regular user")
        ORGANIZATION_ADMIN = "organization_admin", _("Organization admin")
        SUPER_ADMIN = "super_admin", _("Super admin")

    contact_phone = models.CharField(verbose_name=_("Phone number"), blank=True, max_length=100)
    user_role = models.CharField(
        verbose_name=_("User role"), max_length=30, choices=UserRoles.choices, default=UserRoles.REGULAR_USER
    )
    organization = models.ForeignKey(
        "organizations.Organization", verbose_name=_("Organization"), on_delete=models.PROTECT, null=True, blank=True
    )
    avatar = models.ImageField(verbose_name=_("Avatar"), upload_to="avatars/", blank=True)

    @property
    def is_admin(self):
        return self.user_role in {self.UserRoles.ORGANIZATION_ADMIN, self.UserRoles.SUPER_ADMIN}

    @property
    def display_name(self):
        if all([self.first_name, self.last_name]):
            return f"{self.first_name} {self.last_name}"
        else:
            return self.username
