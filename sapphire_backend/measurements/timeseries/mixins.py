from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeSeriesModelMixin(models.Model):
    timestamp = models.DateTimeField(verbose_name=_("Timestamp"), primary_key=True)
    value = models.DecimalField(verbose_name=_("Value"), max_digits=10, decimal_places=5)
    metric = models.CharField(verbose_name=_("Metric"), max_length=30)
    unit = models.CharField(verbose_name=_("Unit"), blank=True, max_length=20)

    class Meta:
        abstract = True
