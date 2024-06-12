from django.db import models
from django.utils.translation import gettext_lazy as _

from .choices import NormType


class NormModelMixin(models.Model):
    ordinal_number = models.PositiveIntegerField(verbose_name=_("Ordinal number"))
    value = models.DecimalField(verbose_name=_("Value"), max_digits=10, decimal_places=5)
    norm_type = models.CharField(
        verbose_name=_("Norm type"), choices=NormType, default=NormType.DECADAL, max_length=20
    )

    class Meta:
        abstract = True
