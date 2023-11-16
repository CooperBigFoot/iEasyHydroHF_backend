from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from timezone_field import TimeZoneField

from sapphire_backend.utils.mixins.models import UUIDMixin


class Organization(UUIDMixin, models.Model):
    class YearType(models.TextChoices):
        CALENDAR = "CA", _("Calendar")
        HYDROLOGICAL = "HY", _("Hydrological")

    class Language(models.TextChoices):
        ENGLISH = "en", _("English")
        RUSSIAN = "ru", _("Russian")

    name = models.CharField(verbose_name=_("Organization name"), max_length=100)
    description = models.TextField(verbose_name=_("Description"), blank=True, default="")
    url = models.URLField(verbose_name=_("Organization URL"), blank=True)

    country = models.CharField(verbose_name=_("Country"), max_length=100)
    city = models.CharField(verbose_name=_("City"), max_length=100)
    street_address = models.CharField(verbose_name=_("Street address"), max_length=255)
    zip_code = models.CharField(verbose_name=_("ZIP code"), max_length=50)
    latitude = models.FloatField(
        verbose_name=_("Latitude"), validators=[MinValueValidator(-90), MaxValueValidator(90)], blank=True, null=True
    )
    longitude = models.FloatField(
        verbose_name=_("Longitude"),
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        blank=True,
        null=True,
    )
    timezone = TimeZoneField(verbose_name=_("Organization timezone"), null=True, blank=True)

    contact = models.CharField(verbose_name=_("Contact person"), max_length=200, blank=True, default="")
    contact_phone = models.CharField(verbose_name=_("Phone number"), blank=True, max_length=100)

    year_type = models.CharField(
        verbose_name=_("Year type"), max_length=2, choices=YearType.choices, default=YearType.HYDROLOGICAL
    )
    language = models.CharField(
        verbose_name=_("Language"), max_length=2, choices=Language.choices, default=Language.ENGLISH
    )

    is_active = models.BooleanField(verbose_name=_("Is active?"), default=True)

    class Meta:
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")
        ordering = ["-name"]
        indexes = [models.Index(fields=["uuid"], name="organization_uuid_idx")]

    def __str__(self):
        return self.name


class Basin(UUIDMixin, models.Model):
    name = models.CharField(verbose_name=_("Basin"), blank=False, max_length=200)
    organization = models.ForeignKey(
        "organizations.Organization",
        to_field="uuid",
        verbose_name=_("Organization"),
        on_delete=models.CASCADE,
        related_name="basins",
    )

    class Meta:
        verbose_name = _("Basin")
        verbose_name_plural = _("Basins")
        ordering = ["-name"]

    def __str__(self):
        return self.name


class Region(UUIDMixin, models.Model):
    name = models.CharField(verbose_name=_("Region"), blank=False, max_length=200)
    organization = models.ForeignKey(
        "organizations.Organization",
        to_field="uuid",
        verbose_name=_("Organization"),
        on_delete=models.CASCADE,
        related_name="regions",
    )

    class Meta:
        verbose_name = _("Region")
        verbose_name_plural = _("Regions")
        ordering = ["-name"]

    def __str__(self):
        return self.name
