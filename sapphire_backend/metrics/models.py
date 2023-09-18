from django.db import models
from django.utils.translation import gettext_lazy as _

from sapphire_backend.metrics.timeseries.mixins import TimeSeriesModelMixin


class WaterDischarge(TimeSeriesModelMixin, models.Model):
    pass

    class Meta:
        verbose_name = _("Water discharge metric")
        verbose_name_plural = _("Water discharge metrics")
        indexes = [models.Index("sensor_id", models.F("timestamp").desc(), name="water_discharge_idx")]

    def __str__(self):
        return f"{self.sensor.name} water discharge reading on {self.timestamp}"


class WaterLevel(TimeSeriesModelMixin, models.Model):
    pass

    class Meta:
        verbose_name = _("Water level metric")
        verbose_name_plural = _("Water level metrics")
        indexes = [models.Index("sensor_id", models.F("timestamp").desc(), name="water_level_idx")]

    def __str__(self):
        return f"{self.sensor.name} water level reading on {self.timestamp}"


class WaterTemperature(TimeSeriesModelMixin, models.Model):
    pass

    class Meta:
        verbose_name = _("Water temperature metric")
        verbose_name_plural = _("Water temperature metrics")
        indexes = [models.Index("sensor_id", models.F("timestamp").desc(), name="water_temperature_idx")]

    def __str__(self):
        return f"{self.sensor.name} water temperature reading on {self.timestamp}"


class WaterVelocity(TimeSeriesModelMixin, models.Model):
    pass

    class Meta:
        verbose_name = _("Water velocity metric")
        verbose_name_plural = _("Water velocity metrics")
        indexes = [models.Index("sensor_id", models.F("timestamp").desc(), name="water_velocity_idx")]

    def __str__(self):
        return f"{self.sensor.name} water velocity reading on {self.timestamp}"


class AirTemperature(TimeSeriesModelMixin, models.Model):
    pass

    class Meta:
        verbose_name = _("Air temperature metric")
        verbose_name_plural = _("Air temperature metrics")
        indexes = [models.Index("sensor_id", models.F("timestamp").desc(), name="air_temperature_idx")]

    def __str__(self):
        return f"{self.sensor.name} air temperature reading on {self.timestamp}"


class Precipitation(TimeSeriesModelMixin, models.Model):
    pass

    class Meta:
        verbose_name = _("Precipitation metric")
        verbose_name_plural = _("Precipitation metrics")
        indexes = [models.Index("sensor_id", models.F("timestamp").desc(), name="precipitation_idx")]

    def __str__(self):
        return f"{self.sensor.name} precipitation reading on {self.timestamp}"


class SensorStatus(models.Model):
    timestamp = models.DateTimeField(primary_key=True, verbose_name=_("Timestamp"))
    sensor = models.ForeignKey("stations.Sensor", verbose_name=_("Sensor"), on_delete=models.PROTECT)
    battery_status = models.DecimalField(
        verbose_name=_("Battery status"), max_digits=10, decimal_places=5, null=True, blank=True
    )
    transmission_signal_power = models.DecimalField(
        verbose_name=_("Transmission signal power"), max_digits=10, decimal_places=5, null=True, blank=True
    )
    malfunction = models.BooleanField(verbose_name=_("Malfunction reported?"), default=False)

    class Meta:
        verbose_name = _("Sensor status metric")
        verbose_name_plural = _("Sensor status metrics")
        indexes = [models.Index("sensor_id", models.F("timestamp").desc(), name="sensor_status_idx")]

    def __str__(self):
        return f"{self.sensor.name} status on {self.timestamp}"
