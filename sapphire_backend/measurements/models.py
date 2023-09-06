from django.db import models
from django.utils.translation import gettext_lazy as _

from sapphire_backend.measurements.timeseries.mixins import TimeSeriesModelMixin


class Measurement(TimeSeriesModelMixin, models.Model):
    station = models.ForeignKey("stations.Station", verbose_name=_("Station"), on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Measurement")
        verbose_name_plural = _("Measurements")
        db_table = "measurement_measurements"
        managed = False  # manually changed to False after the initial migration was run

    def __str__(self):
        return f"{self.station.name} {self.metric} measurement on {self.timestamp}"
