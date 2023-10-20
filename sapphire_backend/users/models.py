from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from sapphire_backend.utils.mixins.models import UUIDMixin


class User(UUIDMixin, AbstractUser):
    class UserRoles(models.TextChoices):
        REGULAR_USER = "regular_user", _("Regular user")
        ORGANIZATION_ADMIN = "organization_admin", _("Organization admin")
        SUPER_ADMIN = "super_admin", _("Super admin")

    class Language(models.TextChoices):
        ENGLISH = "en", _("English")
        RUSSIAN = "ru", _("Russian")

    contact_phone = models.CharField(verbose_name=_("Phone number"), blank=True, max_length=100)
    user_role = models.CharField(
        verbose_name=_("User role"), max_length=30, choices=UserRoles.choices, default=UserRoles.REGULAR_USER
    )
    organization = models.ForeignKey(
        "organizations.Organization",
        verbose_name=_("Organization"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="members",
    )

    avatar = models.ImageField(verbose_name=_("Avatar"), upload_to="avatars/", blank=True)
    is_deleted = models.BooleanField(verbose_name=_("Is deleted?"), default=False)

    language = models.CharField(
        verbose_name=_("Language"), max_length=2, choices=Language.choices, default=Language.ENGLISH
    )

    class Meta(AbstractUser.Meta):
        indexes = [models.Index(fields=["uuid"], name="user_uuid_idx")]

    @property
    def is_admin(self):
        return self.user_role in {self.UserRoles.ORGANIZATION_ADMIN, self.UserRoles.SUPER_ADMIN}

    @property
    def is_organization_admin(self):
        return self.user_role == self.UserRoles.ORGANIZATION_ADMIN

    @property
    def is_superadmin(self):
        return self.user_role == self.UserRoles.SUPER_ADMIN

    @property
    def is_regular(self):
        return self.user_role == self.UserRoles.REGULAR_USER

    @property
    def display_name(self):
        if all([self.first_name, self.last_name]):
            return f"{self.first_name} {self.last_name}"
        else:
            return self.username

    def soft_delete(self):
        self.is_deleted = True
        self.username = f"User {self.uuid}"
        self.email = "deleted@user.com"
        self.is_active = False
        self.organization = None
        self.save()
