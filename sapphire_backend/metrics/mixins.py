from django.db import models
from django.utils.translation import gettext_lazy as _

from .choices import HydrologicalMeasurementType, HydrologicalMetricName, MetricUnit, NormType


class NormModelMixin(models.Model):
    ordinal_number = models.PositiveIntegerField(verbose_name=_("Ordinal number"))
    value = models.DecimalField(verbose_name=_("Value"), max_digits=10, decimal_places=5)
    norm_type = models.CharField(
        verbose_name=_("Norm type"), choices=NormType, default=NormType.DECADAL, max_length=20
    )

    class Meta:
        abstract = True


class SensorInfoMixin(models.Model):
    sensor_identifier = models.CharField(verbose_name=_("Sensor identifier"), blank=True, max_length=50)
    sensor_type = models.CharField(verbose_name=_("Sensor type"), blank=True, max_length=50)

    class Meta:
        abstract = True


class MinMaxValueMixin(models.Model):
    min_value = models.DecimalField(
        verbose_name=_("Minimum value"), max_digits=15, decimal_places=5, null=True, blank=True
    )
    max_value = models.DecimalField(
        verbose_name=_("Maximum value"), max_digits=15, decimal_places=5, null=True, blank=True
    )

    class Meta:
        abstract = True


class BaseHydroMetricMixin(models.Model):
    timestamp_local = models.DateTimeField(primary_key=True, verbose_name=_("Timestamp local without timezone"))
    avg_value = models.DecimalField(verbose_name=_("Average value"), max_digits=15, decimal_places=5)
    unit = models.CharField(verbose_name=_("Unit"), choices=MetricUnit, blank=True, max_length=20)
    value_type = models.CharField(
        verbose_name=_("Value type"),
        choices=HydrologicalMeasurementType,
        default=HydrologicalMeasurementType.UNKNOWN,
        max_length=2,
        blank=False,
    )
    metric_name = models.CharField(
        verbose_name=_("Metric name"),
        choices=HydrologicalMetricName,
        max_length=20,
        blank=False,
    )

    class Meta:
        abstract = True
