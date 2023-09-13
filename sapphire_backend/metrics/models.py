from django.db import models
from django.utils.translation import gettext_lazy as _

from sapphire_backend.metrics.timeseries.mixins import TimeSeriesModelMixin


class WaterDischarge(TimeSeriesModelMixin, models.Model):
    pass

    class Meta:
        verbose_name = _("Water discharge metric")
        verbose_name_plural = _("Water discharge metrics")
        indexes = [models.Index("station_id", models.F("timestamp").desc(), name="water_discharge_idx")]

    def __str__(self):
        return f"{self.station.name} water discharge reading on {self.timestamp}"


class WaterLevel(TimeSeriesModelMixin, models.Model):
    pass

    class Meta:
        verbose_name = _("Water level metric")
        verbose_name_plural = _("Water level metrics")
        indexes = [models.Index("station_id", models.F("timestamp").desc(), name="water_level_idx")]

    def __str__(self):
        return f"{self.station.name} water level reading on {self.timestamp}"


class WaterTemperature(TimeSeriesModelMixin, models.Model):
    pass

    class Meta:
        verbose_name = _("Water temperature metric")
        verbose_name_plural = _("Water temperature metrics")
        indexes = [models.Index("station_id", models.F("timestamp").desc(), name="water_temperature_idx")]

    def __str__(self):
        return f"{self.station.name} water temperature reading on {self.timestamp}"


class WaterVelocity(TimeSeriesModelMixin, models.Model):
    pass

    class Meta:
        verbose_name = _("Water velocity metric")
        verbose_name_plural = _("Water velocity metrics")
        indexes = [models.Index("station_id", models.F("timestamp").desc(), name="water_velocity_idx")]

    def __str__(self):
        return f"{self.station.name} water velocity reading on {self.timestamp}"


class AirTemperature(TimeSeriesModelMixin, models.Model):
    pass

    class Meta:
        verbose_name = _("Air temperature metric")
        verbose_name_plural = _("Air temperature metrics")
        indexes = [models.Index("station_id", models.F("timestamp").desc(), name="air_temperature_idx")]

    def __str__(self):
        return f"{self.station.name} air temperature reading on {self.timestamp}"
