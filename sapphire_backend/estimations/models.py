from django.db import models
from django.utils.translation import gettext_lazy as _

from sapphire_backend.metrics.managers import HydrologicalNormQuerySet
from sapphire_backend.metrics.mixins import NormModelMixin
from sapphire_backend.utils.mixins.models import UUIDMixin


class DischargeModel(UUIDMixin, models.Model):
    name = models.CharField(verbose_name=_("Discharge model name"), max_length=100, blank=False)
    param_a = models.DecimalField(verbose_name=_("Parameter a"), max_digits=50, decimal_places=30)
    param_b = models.DecimalField(verbose_name=_("Parameter b"), max_digits=50, decimal_places=30)
    param_c = models.DecimalField(verbose_name=_("Parameter c"), max_digits=50, decimal_places=30)
    valid_from_local = models.DateTimeField()
    station = models.ForeignKey("stations.HydrologicalStation", verbose_name=_("Station"), on_delete=models.PROTECT)

    class Meta:
        verbose_name = _("Discharge model")
        verbose_name_plural = _("Discharge models")
        ordering = ["-valid_from_local"]

    def __str__(self):
        return f"DischargeModel ({self.name}): Q = {self.param_c} (H + {self.param_a} ) ^ {self.param_b}, valid from local: {self.valid_from_local}"

    def estimate_discharge(self, water_level):
        return float(self.param_c) * (float(water_level) + float(self.param_a)) ** float(self.param_b)


class HydrologicalNormVirtual(NormModelMixin, models.Model):
    station = models.ForeignKey(
        "stations.VirtualStation",
        to_field="uuid",
        verbose_name=_("Virtual station"),
        on_delete=models.CASCADE,
    )
    objects = HydrologicalNormQuerySet.as_manager()

    class Meta:
        managed = False
        db_table = "estimations_hydrologicalnorm_virtual"
