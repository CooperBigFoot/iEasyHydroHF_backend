from django.db import models
from django.utils.translation import gettext_lazy as _

from sapphire_backend.utils.mixins.models import UUIDMixin


class DischargeModel(UUIDMixin, models.Model):
    name = models.CharField(verbose_name=_("Organization name"), max_length=100, blank=False)
    param_a = models.DecimalField(verbose_name=_("Parameter a"), max_digits=50, decimal_places=30)
    param_b = models.DecimalField(verbose_name=_("Parameter b"), max_digits=50, decimal_places=30)
    param_c = models.DecimalField(verbose_name=_("Parameter c"), max_digits=50, decimal_places=30)
    valid_from = models.DateTimeField()
    station = models.ForeignKey("stations.HydrologicalStation", verbose_name=_("Station"), on_delete=models.PROTECT)

    class Meta:
        verbose_name = _("Discharge model")
        verbose_name_plural = _("Discharge models")
        ordering = ["-valid_from"]

    def __str__(self):
        return f"DischargeModel ({self.name}): Q = {self.param_c} (H + {self.param_a} ) ^ {self.param_b}, valid from: {self.valid_from}"

    def estimate_discharge(self, water_level):
        return float(self.param_c) * (float(water_level) + float(self.param_a)) ** float(self.param_b)
