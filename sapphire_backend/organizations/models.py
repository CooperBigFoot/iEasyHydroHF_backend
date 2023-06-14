from timezone_field import TimeZoneField
from phonenumber_field.modelfields import PhoneNumberField

from django.db import models
from django.utils.translation import gettext_lazy as _


class Organization(models.Model):
    class YearType(models.TextChoices):
        CALENDAR = "CA", _("Calendar")
        HYDROLOGICAL = "HY", _("Hydrological")

    name = models.CharField(verbose_name=_("Organization name"), max_length=100)
    description = models.TextField(verbose_name=_("Description"), blank=True, default="")
    url = models.URLField(verbose_name=_("Organization URL"), blank=True)

    country = models.CharField(verbose_name=_("Country"), max_length=100)
    city = models.CharField(verbose_name=_("City"), max_length=100)
    street_address = models.CharField(verbose_name=_("Street address"), max_length=255)
    zip_code = models.CharField(verbose_name=_("ZIP code"), max_length=50)
    timezone = TimeZoneField(verbose_name=_("Organization timezone"), null=True, blank=True)

    contact = models.CharField(verbose_name=_("Contact person"), max_length=200, blank=True, default="")
    contact_phone = PhoneNumberField(verbose_name=_("Contact phone"), blank=True)

    year_type = models.CharField(
        verbose_name=_("Year type"), max_length=2, choices=YearType.choices, default=YearType.HYDROLOGICAL
    )

    active = models.BooleanField(verbose_name=_("Is active?"), default=True)
    deleted = models.BooleanField(verbose_name=_("Is deleted?"), default=False)

    class Meta:
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")
        ordering = ["-name"]
