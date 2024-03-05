from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from timezone_field import TimeZoneField


class LocationMixin(models.Model):
    country = models.CharField(verbose_name=_("Country"), max_length=100)
    organization = models.ForeignKey(
        "organizations.Organization",
        to_field="uuid",
        verbose_name=_("Organization"),
        on_delete=models.PROTECT,
        related_name="%(class)s_related",
    )
    basin = models.ForeignKey(
        "organizations.Basin",
        to_field="uuid",
        verbose_name=_("Basin"),
        on_delete=models.PROTECT,
        related_name="%(class)s_related",
        null=True,
        blank=False,
    )
    region = models.ForeignKey(
        "organizations.Region",
        to_field="uuid",
        verbose_name=_("Region"),
        on_delete=models.PROTECT,
        related_name="%(class)s_related",
        null=True,
        blank=False,
    )
    latitude = models.FloatField(
        verbose_name=_("Latitude"), validators=[MinValueValidator(-90), MaxValueValidator(90)], null=True, blank=True
    )
    longitude = models.FloatField(
        verbose_name=_("Longitude"),
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        null=True,
        blank=True,
    )
    timezone = TimeZoneField(verbose_name=_("Station timezone"), null=True, blank=True)
    elevation = models.FloatField(verbose_name=_("Elevation in meters"), blank=True, null=True)

    class Meta:
        abstract = True
