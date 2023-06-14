from timezone_field import TimeZoneField

from django.db import models
from django.utils.translation import gettext_lazy as _


class Organization(models.Model):
    name = models.CharField(verbose_name=_("Organization name"), max_length=100)
    country = models.CharField(verbose_name=_("Country"), max_length=100)
    city = models.CharField(verbose_name=_("City"), max_length=100)
    street_address = models.CharField(verbose_name=_("Street address"), max_length=255)
    zip_code = models.CharField(verbose_name=_("ZIP code"), max_length=50)
    timezone = TimeZoneField(verbose_name=_("Organization timezone"), null=True, blank=True)
