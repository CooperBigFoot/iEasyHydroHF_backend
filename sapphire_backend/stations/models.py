from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from timezone_field import TimeZoneField

from sapphire_backend.utils.mixins.models import SlugMixin, UUIDMixin

from .managers import SensorQuerySet


class Station(SlugMixin, UUIDMixin, models.Model):
    class StationType(models.TextChoices):
        HYDROLOGICAL = "H", _("Hydrological")
        METEOROLOGICAL = "M", _("Meteorological")

    name = models.CharField(verbose_name=_("Station name"), max_length=150)
    description = models.TextField(verbose_name=_("Description"), blank=True)
    station_type = models.CharField(
        verbose_name=_("Station type"), choices=StationType.choices, default=StationType.HYDROLOGICAL
    )
    organization = models.ForeignKey(
        "organizations.Organization",
        to_field="uuid",
        verbose_name=_("Organization"),
        on_delete=models.PROTECT,
        related_name="stations",
    )
    station_code = models.CharField(verbose_name=_("Station code"), max_length=100)

    country = models.CharField(verbose_name=_("Country"), max_length=100)
    basin = models.ForeignKey(
        "organizations.Basin",
        to_field="uuid",
        verbose_name=_("Basin"),
        on_delete=models.PROTECT,
        related_name="stations",
        null=True,
        blank=False,
    )
    region = models.ForeignKey(
        "organizations.Region",
        to_field="uuid",
        verbose_name=_("Region"),
        on_delete=models.PROTECT,
        related_name="regions",
        null=True,
        blank=False,
    )
    latitude = models.FloatField(
        verbose_name=_("Latitude"), validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )
    longitude = models.FloatField(
        verbose_name=_("Longitude"), validators=[MinValueValidator(-180), MaxValueValidator(180)]
    )
    timezone = TimeZoneField(verbose_name=_("Station timezone"), null=True, blank=True)
    elevation = models.FloatField(verbose_name=_("Elevation in meters"), blank=True, null=True)

    is_automatic = models.BooleanField(verbose_name=_("Is automatic station?"), default=False)
    is_deleted = models.BooleanField(verbose_name=_("Is deleted?"), default=False)
    is_virtual = models.BooleanField(verbose_name=_("Is virtual?"), default=False)
    measurement_time_step = models.IntegerField(
        verbose_name=_("Measurement time step in minutes"), blank=True, null=True
    )
    discharge_level_alarm = models.FloatField(verbose_name=_("Dangerous discharge level"), blank=True, null=True)

    class Meta:
        verbose_name = _("Station")
        verbose_name_plural = _("Stations")
        ordering = ["-name"]
        indexes = [
            models.Index(fields=["organization"], name="station_organization_idx"),
            models.Index(fields=["station_code"], name="station_code_idx"),
            models.Index(fields=["uuid"], name="station_uuid_idx"),
            models.Index(fields=["basin"], name="station_basin_idx"),
        ]
        constraints = [
            models.UniqueConstraint("station_code", "is_automatic", name="station_code_is_automatic_unique")
        ]

    def __str__(self):
        return self.name


class Sensor(UUIDMixin, models.Model):
    name = models.CharField(verbose_name=_("Sensor name"), default="Default", max_length=100)
    manufacturer = models.CharField(verbose_name=_("Manufacturer"), max_length=150, blank=True)
    identifier = models.CharField(verbose_name=_("Sensor identifier"), max_length=150, blank=True)
    station = models.ForeignKey(
        "stations.Station",
        to_field="uuid",
        verbose_name=_("Station"),
        on_delete=models.PROTECT,
        related_name="sensors",
    )
    installation_date = models.DateTimeField(verbose_name=_("Installation date"), blank=True, null=True)
    is_active = models.BooleanField(verbose_name=_("Is active?"), default=True)
    is_default = models.BooleanField(verbose_name=_("Is default?"), default=True)

    objects = SensorQuerySet.as_manager()

    class Meta:
        verbose_name = _("Sensor")
        verbose_name_plural = _("Sensors")
        ordering = ["-name"]
        indexes = [
            models.Index(fields=["uuid"], name="sensor_uuid_idx"),
            models.Index(fields=["station"], name="sensor_station_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["station", "is_default"],
                name="unique_default_sensor_per_station",
                condition=models.Q(is_default=True),
            )
        ]

    def __str__(self):
        return f"{self.name} sensor - {self.station.name} station"
