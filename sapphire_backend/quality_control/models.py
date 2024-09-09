from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from sapphire_backend.utils.mixins.models import CreatedDateMixin

from .choices import HistoryLogEntryType


class HistoryLog(models.Model):
    hydro_metric = models.ForeignKey(
        "metrics.HydrologicalMetric", on_delete=models.CASCADE, related_name="history_log", null=True, blank=True
    )
    meteo_metric = models.ForeignKey(
        "metrics.MeteorologicalMetric", on_delete=models.CASCADE, related_name="history_log", null=True, blank=True
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(hydro_metric__isnull=False) | Q(meteo_metric__isnull=False), name="check_one_metric_populated"
            ),
            models.UniqueConstraint(fields=["hydro_metric"], name="unique_hydro_metric_history_log"),
            models.UniqueConstraint(fields=["meteo_metric"], name="unique_meteo_metric_history_log"),
        ]
        verbose_name = _("History Log")
        verbose_name_plural = _("History Logs")

    @property
    def metric(self):
        return self.hydro_metric or self.meteo_metric

    @property
    def metric_value(self):
        if self.hydro_metric:
            return self.hydro_metric.avg_value
        else:
            return self.meteo_metric.value

    def create_entry(self, entry_type: HistoryLogEntryType, src_id: int, description: str = None):
        entry = HistoryLogEntry.objects.create(
            history_log=self, value=self.metric_value, description=description, type=entry_type, source_id=src_id
        )

        return entry

    def get_initial_log(self):
        return self.entries.first()

    def get_latest_log(self):
        return self.entries.last()


class HistoryLogEntry(CreatedDateMixin, models.Model):
    history_log = models.ForeignKey(
        HistoryLog, verbose_name=_("History log"), on_delete=models.CASCADE, related_name="entries"
    )
    value = models.DecimalField(verbose_name=_("Value"), max_digits=10, decimal_places=5)
    source_id = models.PositiveIntegerField(verbose_name=_("Source"))
    type = models.CharField(
        verbose_name=_("Value type"), choices=HistoryLogEntryType, default=HistoryLogEntryType.TELEGRAM, max_length=2
    )
    description = models.TextField(verbose_name=_("Description"), blank=True)

    class Meta:
        verbose_name = _("History log entry")
        verbose_name_plural = _("History log entries")
        ordering = ["-created_date"]
