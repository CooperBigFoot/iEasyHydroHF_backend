from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeSeriesModelMixin(models.Model):
    timestamp = models.DateTimeField(primary_key=True, verbose_name=_("Timestamp"))
    value = models.DecimalField(verbose_name=_("Value"), max_digits=10, decimal_places=5, null=True, blank=True)
    unit = models.CharField(verbose_name=_("Unit"), blank=True, max_length=20)
    station = models.ForeignKey("stations.Station", verbose_name=_("Station"), on_delete=models.CASCADE)

    class Meta:
        abstract = True
