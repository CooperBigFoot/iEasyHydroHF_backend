from django.db import models
from django.utils.translation import gettext_lazy as _

from sapphire_backend.utils.mixins.models import CreatedDateMixin, SourceTypeMixin

from .choices import HistoryLogStationType


class HistoryLogEntry(CreatedDateMixin, models.Model):
    # metric PK fields
    timestamp_local = models.DateTimeField(verbose_name=_("Timestamp local without timezone"))
    station_id = models.PositiveIntegerField(verbose_name=_("Station ID"))
    metric_name = models.CharField(verbose_name=_("Metric name"), max_length=10)
    value_type = models.CharField(verbose_name=_("Value type"), max_length=10)
    sensor_identifier = models.CharField(verbose_name=_("Sensor identifier"), max_length=50, blank=True)
    station_type = models.CharField(
        verbose_name=_("Station type"),
        choices=HistoryLogStationType,
        default=HistoryLogStationType.HYDRO,
        max_length=50,
    )

    # previous state
    previous_value = models.DecimalField(verbose_name=_("Previous value"), max_digits=10, decimal_places=5)
    previous_value_code = models.IntegerField(verbose_name=_("Previous code"), blank=True, null=True)
    previous_source_type = models.CharField(
        verbose_name=_("Previous source type"), max_length=2, choices=SourceTypeMixin.SourceType
    )
    previous_source_id = models.IntegerField(verbose_name=_("Previous source ID"))

    # new state
    new_value = models.DecimalField(verbose_name=_("New value"), max_digits=10, decimal_places=5)
    new_value_code = models.IntegerField(verbose_name=_("New code"), blank=True, null=True)
    new_source_type = models.CharField(
        verbose_name=_("New source type"), max_length=2, choices=SourceTypeMixin.SourceType
    )
    new_source_id = models.IntegerField(verbose_name=_("New source ID"))

    # description fields
    description = models.TextField(verbose_name=_("Description"), blank=True)

    class Meta:
        verbose_name = _("History log entry")
        verbose_name_plural = _("History log entries")
        ordering = ["-created_date"]

    def __str__(self):
        return f"Log entry for station {self.station_id} on {self.created_date}"
