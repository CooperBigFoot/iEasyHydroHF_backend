from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from sapphire_backend.utils.mixins.models import CreatedDateMixin, UUIDMixin


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
        to_field="uuid",
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


class UserAssignedStation(CreatedDateMixin, models.Model):
    user = models.ForeignKey(
        "users.User",
        to_field="uuid",
        verbose_name=_("User"),
        on_delete=models.PROTECT,
        related_name="assigned_stations",
    )
    hydro_station = models.ForeignKey(
        "stations.HydrologicalStation",
        to_field="uuid",
        verbose_name=_("Hydrological station"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_users",
    )
    meteo_station = models.ForeignKey(
        "stations.MeteorologicalStation",
        to_field="uuid",
        verbose_name=_("Meteorological station"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_users",
    )
    virtual_station = models.ForeignKey(
        "stations.VirtualStation",
        to_field="uuid",
        verbose_name=_("Virtual station"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_users",
    )
    assigned_by = models.ForeignKey(
        "users.User", to_field="uuid", verbose_name=_("Assigned by"), null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = _("User assigned station")
        verbose_name_plural = _("User assigned stations")
        ordering = ["-created_date"]
        constraints = [
            models.CheckConstraint(
                check=(
                    Q(hydro_station__isnull=False, meteo_station__isnull=True, virtual_station__isnull=True)
                    | Q(hydro_station__isnull=True, meteo_station__isnull=False, virtual_station__isnull=True)
                    | Q(hydro_station__isnull=True, meteo_station__isnull=True, virtual_station__isnull=False)
                ),
                name="only_one_station_populated",
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.station.name}"

    @property
    def station(self):
        return self.hydro_station or self.meteo_station or self.virtual_station

    def clean(self):
        super().clean()
        if not self.station:
            raise ValidationError(_("You must assign a station"))
        station_organization = (
            self.station.site.organization if hasattr(self.station, "site") else self.station.organization
        )
        if self.user.is_superadmin is not True and self.user.organization != station_organization:
            raise ValidationError(_("The assigned station and user must be in the same organization"))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
