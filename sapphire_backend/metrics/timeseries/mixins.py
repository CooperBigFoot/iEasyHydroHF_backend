import logging
from datetime import timedelta

from django.db import models
from django.db.utils import IntegrityError
from django.utils.translation import gettext_lazy as _

from sapphire_backend.metrics.managers import TimeSeriesManager

logger = logging.getLogger("timeseries_logger")


class TimeSeriesModelMixin(models.Model):
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
    sensor = models.ForeignKey("stations.Sensor", to_field="uuid", verbose_name=_("Sensor"), on_delete=models.PROTECT)

    objects = TimeSeriesManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
        except IntegrityError as e:
            logger.exception(e)
            self.timestamp += timedelta(microseconds=1)
            self.save(*args, **kwargs)
