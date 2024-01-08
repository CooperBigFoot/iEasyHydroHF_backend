from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from timezone_field import TimeZoneField

from sapphire_backend.utils.mixins.models import CreateLastModifiedDateMixin, ForecastToggleMixin, UUIDMixin

User = get_user_model()


class Site(UUIDMixin, models.Model):
    name = models.CharField(verbose_name=_("Name"), blank=False, max_length=150)
    organization = models.ForeignKey(
        "organizations.Organization",
        to_field="uuid",
        verbose_name=_("Organization"),
        on_delete=models.PROTECT,
        related_name="stations",
    )
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

    class Meta:
        verbose_name = _("Site")
        verbose_name_plural = _("Sites")
        ordering = ["name"]
        indexes = [models.Index("uuid", name="site_uuid_idx")]

    def __str__(self):
        return self.name


class HydrologicalStation(UUIDMixin, ForecastToggleMixin, models.Model):
    class StationType(models.TextChoices):
        MANUAL = "M", _("Manual")
        AUTOMATIC = "A", _("Automatic")

    name = models.CharField(verbose_name=_("Station name"), blank=True, max_length=150)
    station_code = models.CharField(verbose_name=_("Station code"), max_length=100, blank=True)
    station_type = models.CharField(
        verbose_name=_("Station type"), choices=StationType, default=StationType.MANUAL, max_length=2, blank=False
    )
    description = models.TextField(verbose_name=_("Description"), blank=True)
    site = models.ForeignKey(
        "stations.Site",
        verbose_name=_("Site"),
        to_field="uuid",
        on_delete=models.PROTECT,
        null=False,
        blank=False,
        related_name="hydro_stations",
    )
    measurement_time_step = models.IntegerField(
        verbose_name=_("Measurement time step in minutes"), blank=True, null=True
    )
    discharge_level_alarm = models.FloatField(verbose_name=_("Dangerous discharge level"), blank=True, null=True)
    historical_discharge_minimum = models.FloatField(
        verbose_name=_("Historical minimal value of discharge"), blank=True, null=True
    )
    historical_discharge_maximum = models.FloatField(
        verbose_name=_("Historical maximal value of discharge"), blank=True, null=True
    )
    decadal_discharge_norm = models.FloatField(verbose_name=_("Decadal discharge norm"), blank=True, null=True)
    monthly_discharge_norm = models.JSONField(verbose_name=_("Monthly discharge norm"), blank=True, null=True)
    is_deleted = models.BooleanField(verbose_name=_("Is deleted?"), default=False)
    bulletin_order = models.PositiveIntegerField(verbose_name=_("Bulletin order"), default=0)

    class Meta:
        verbose_name = _("Hydrological station")
        verbose_name_plural = _("Hydrological stations")
        constraints = [
            models.UniqueConstraint("station_code", "station_type", name="hydro_station_code_type_unique_cn")
        ]
        indexes = [models.Index("uuid", name="hydro_station_uuid_idx")]

    def __str__(self):
        return self.name or self.site.name


class MeteorologicalStation(UUIDMixin, models.Model):
    class StationType(models.TextChoices):
        MANUAL = "M", _("Manual")
        AUTOMATIC = "A", _("Automatic")

    name = models.CharField(verbose_name=_("Station name"), blank=True, max_length=150)
    station_code = models.CharField(verbose_name=_("Station code"), max_length=100, blank=True)
    station_type = models.CharField(
        verbose_name=_("Station type"), choices=StationType, default=StationType.MANUAL, max_length=2, blank=False
    )
    site = models.ForeignKey(
        "stations.Site",
        verbose_name=_("Site"),
        to_field="uuid",
        on_delete=models.PROTECT,
        null=False,
        blank=False,
        related_name="meteo_stations",
    )
    description = models.TextField(verbose_name=_("Description"), blank=True)
    is_deleted = models.BooleanField(verbose_name=_("Is deleted?"), default=False)

    class Meta:
        verbose_name = _("Meteorological station")
        verbose_name_plural = _("Meteorological stations")
        constraints = [models.UniqueConstraint("station_code", name="meteo_station_code_unique_cn")]
        indexes = [models.Index("uuid", name="meteo_station_uuid_idx")]

    def __str__(self):
        return self.name or self.site.name


class Remark(UUIDMixin, CreateLastModifiedDateMixin, models.Model):
    comment = models.TextField(verbose_name=_("Comment"), blank=False)
    user = models.ForeignKey(
        User, to_field="uuid", on_delete=models.SET_NULL, null=True, blank=True, related_name="remarks"
    )
    hydro_station = models.ForeignKey(
        "stations.HydrologicalStation",
        verbose_name=_("Hydrological station"),
        to_field="uuid",
        on_delete=models.CASCADE,
        related_name="remarks",
        null=True,
        blank=True,
    )
    meteo_station = models.ForeignKey(
        "stations.MeteorologicalStation",
        verbose_name=_("Meteorological station"),
        to_field="uuid",
        on_delete=models.CASCADE,
        related_name="remarks",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Remark")
        verbose_name_plural = _("Remarks")
        ordering = ["-last_modified"]
        constraints = [
            models.CheckConstraint(
                check=(
                    Q(meteo_station__isnull=False, hydro_station__isnull=True)
                    | Q(meteo_station__isnull=True, hydro_station__isnull=False)
                ),
                name="remark_has_hydro_or_meteo_station_set",
            )
        ]

    def __str__(self):
        return self.comment[:50]

    @property
    def station(self):
        return self.hydro_station or self.meteo_station
