import logging

from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from sapphire_backend.metrics.managers import TimeSeriesManager

logger = logging.getLogger("timeseries_logger")


class TimeSeriesModelMixin(models.Model):
    class MeasurementType(models.TextChoices):
        MANUAL = "M", _("Manual")
        AUTOMATIC = "A", _("Automatic")
        CALCULATED = "C", _("Calculated")
        IMPORTED = "I", _("Imported")
        UNKNOWN = "U", _("Unknown")

    timestamp = models.DateTimeField(primary_key=True, verbose_name=_("Timestamp"))
    minimum_value = models.DecimalField(
        verbose_name=_("Minimum value"), max_digits=10, decimal_places=5, null=True, blank=True
    )
    average_value = models.DecimalField(
        verbose_name=_("Average value"), max_digits=10, decimal_places=5, null=True, blank=True
    )
    maximum_value = models.DecimalField(
        verbose_name=_("Maximum value"), max_digits=10, decimal_places=5, null=True, blank=True
    )
    unit = models.CharField(verbose_name=_("Unit"), blank=True, max_length=20)
    value_type = models.CharField(
        verbose_name=_("Value type"),
        choices=MeasurementType,
        default=MeasurementType.UNKNOWN,
        max_length=2,
        blank=False,
    )
    hydro_station = models.ForeignKey(
        "stations.HydrologicalStation",
        verbose_name=_("Hydrological station"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    meteo_station = models.ForeignKey(
        "stations.MeteorologicalStation",
        verbose_name=_("Meteorological station"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    sensor_identifier = models.CharField(verbose_name=_("Sensor identifier"), blank=True, max_length=50)
    sensor_type = models.CharField(verbose_name=_("Sensor type"), blank=True, max_length=50)

    objects = TimeSeriesManager()

    class Meta:
        abstract = True
        constraints = [
            models.CheckConstraint(
                check=(
                    Q(meteo_station__isnull=False, hydro_station__is_null=True)
                    | Q(meteo_station__isnull=True, hydro_station__is_null=False)
                ),
                name="metric_has_hydro_or_meteo_station_set",
            ),
            models.UniqueConstraint(
                "timestamp", "hydro_station", "meteo_station", "sensor_identifier", name="metric_unique_constraint"
            ),
        ]

    def __str__(self):
        return f"{self.station.name} - {self.timestamp}"

    @property
    def station(self):
        return self.hydro_station or self.meteo_station
