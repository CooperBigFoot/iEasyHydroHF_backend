from django.db import models
from django.utils.translation import gettext_lazy as _


class HydrologicalMetric(models.Model):
    class MeasurementType(models.TextChoices):
        MANUAL = "M", _("Manual")
        AUTOMATIC = "A", _("Automatic")
        CALCULATED = "C", _("Calculated")
        IMPORTED = "I", _("Imported")
        UNKNOWN = "U", _("Unknown")

    class MetricName(models.TextChoices):
        WATER_DISCHARGE = "WD", _("Water discharge")
        WATER_LEVEL = "WL", _("Water level")
        WATER_VELOCITY = "WV", _("Water velocity")
        WATER_TEMPERATURE = "WT", _("Water temperature")
        AIR_TEMPERATURES = "AT", _("Air temperature")
        PRECIPITATION = "PC", _("Precipitation")

    timestamp = models.DateTimeField(primary_key=True, verbose_name=_("Timestamp"))
    min_value = models.DecimalField(
        verbose_name=_("Minimum value"), max_digits=10, decimal_places=5, null=True, blank=True
    )
    avg_value = models.DecimalField(verbose_name=_("Average value"), max_digits=10, decimal_places=5)
    max_value = models.DecimalField(
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
    metric_name = models.CharField(
        verbose_name=_("Metric name"),
        choices=MetricName,
        max_length=2,
        blank=False,
    )
    station = models.ForeignKey("stations.HydrologicalStation", verbose_name=_("Station"), on_delete=models.PROTECT)

    sensor_identifier = models.CharField(verbose_name=_("Sensor identifier"), blank=True, max_length=50)
    sensor_type = models.CharField(verbose_name=_("Sensor type"), blank=True, max_length=50)

    class Meta:
        verbose_name = _("Hydrological metric")
        verbose_name_plural = _("Hydrological metrics")
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.metric_name}, {self.station.name} on {self.timestamp}"


class MeteorologicalMetric(models.Model):
    class MetricName(models.TextChoices):
        AIR_TEMPERATURES = "AT", _("Air temperature")
        PRECIPITATION = "PC", _("Precipitation")

    timestamp = models.DateTimeField(primary_key=True, verbose_name=_("Timestamp"))
    value = models.DecimalField(verbose_name=_("Value"), max_digits=10, decimal_places=5)
    metric_name = models.CharField(
        verbose_name=_("Metric name"),
        choices=MetricName,
        max_length=2,
        blank=False,
    )
    unit = models.CharField(verbose_name=_("Unit"), blank=True, max_length=20)
    station = models.ForeignKey("stations.MeteorologicalStation", verbose_name=_("Station"), on_delete=models.PROTECT)

    class Meta:
        verbose_name = _("Meteorological metric")
        verbose_name_plural = _("Meteorological metrics")
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.metric_name}, {self.station.name} on {self.timestamp}"
