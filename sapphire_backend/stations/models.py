from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from sapphire_backend.utils.mixins.models import CreateLastModifiedDateMixin, ForecastToggleMixin, UUIDMixin

from .managers import HydroStationQuerySet, MeteoStationQuerySet, VirtualStationQuerySet
from .mixins import LocationMixin

User = get_user_model()


class Site(UUIDMixin, LocationMixin, models.Model):
    pass

    class Meta:
        verbose_name = _("Site")
        verbose_name_plural = _("Sites")
        indexes = [models.Index("uuid", name="site_uuid_idx")]

    def __str__(self):
        return str(self.uuid)


class HydrologicalStation(UUIDMixin, ForecastToggleMixin, models.Model):
    class StationType(models.TextChoices):
        MANUAL = "M", _("Manual")
        AUTOMATIC = "A", _("Automatic")

    name = models.CharField(verbose_name=_("Station name"), max_length=150)
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
    station_code = models.CharField(verbose_name=_("Station code"), max_length=100, blank=False)
    station_type = models.CharField(
        verbose_name=_("Station type"), choices=StationType, default=StationType.MANUAL, max_length=2, blank=False
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

    objects = HydroStationQuerySet.as_manager()

    class Meta:
        verbose_name = _("Hydrological station")
        verbose_name_plural = _("Hydrological stations")
        constraints = [
            models.UniqueConstraint("station_code", "station_type", name="hydro_station_code_type_unique_cn")
        ]
        indexes = [models.Index("uuid", name="hydro_station_uuid_idx")]

    def __str__(self):
        return self.name


class MeteorologicalStation(UUIDMixin, models.Model):
    name = models.CharField(verbose_name=_("Station name"), blank=False, max_length=150)
    station_code = models.CharField(verbose_name=_("Station code"), max_length=100, blank=False)
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

    objects = MeteoStationQuerySet.as_manager()

    class Meta:
        verbose_name = _("Meteorological station")
        verbose_name_plural = _("Meteorological stations")
        constraints = [models.UniqueConstraint("station_code", name="meteo_station_code_unique_cn")]
        indexes = [models.Index("uuid", name="meteo_station_uuid_idx")]

    def __str__(self):
        return self.name


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


class VirtualStation(UUIDMixin, LocationMixin, models.Model):
    name = models.CharField(verbose_name=_("Virtual station name"), blank=False, max_length=150)
    description = models.TextField(verbose_name=_("Description"), blank=True)
    station_code = models.CharField(verbose_name=_("Station code"), max_length=100, blank=False)
    hydro_stations = models.ManyToManyField(
        "stations.HydrologicalStation", through="stations.VirtualStationAssociation", related_name="virtual_stations"
    )
    is_deleted = models.BooleanField(verbose_name=_("Is deleted?"), default=False)

    objects = VirtualStationQuerySet.as_manager()

    class Meta:
        verbose_name = _("Virtual station")
        verbose_name_plural = _("Virtual stations")
        indexes = [models.Index("uuid", name="virtual_station_uuid_idx")]

    def __str__(self):
        return self.name


class VirtualStationAssociation(CreateLastModifiedDateMixin, models.Model):
    virtual_station = models.ForeignKey(
        "stations.VirtualStation", verbose_name=_("Virtual station"), on_delete=models.CASCADE
    )
    hydro_station = models.ForeignKey(
        "stations.HydrologicalStation", verbose_name=_("Hydrological station"), on_delete=models.CASCADE
    )
    weight = models.DecimalField(verbose_name=_("Weight"), max_digits=5, decimal_places=2)

    class Meta:
        verbose_name = _("Virtual station association")
        verbose_name_plural = _("Virtual station associations")

    def __str__(self):
        return f"{self.virtual_station.name} - {self.hydro_station.name}"
