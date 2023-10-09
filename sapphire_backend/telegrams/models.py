from django.db import models
from django.utils.translation import gettext_lazy as _

from sapphire_backend.utils.mixins.models import CreatedDateMixin


class Telegram(CreatedDateMixin, models.Model):
    telegram = models.TextField(verbose_name=_("Original telegram(s)"))
    decoded_values = models.JSONField(verbose_name=_("Decoded values"), blank=True, null=True)
    automatically_ingested = models.BooleanField(verbose_name=_("Was automatically ingested?"), default=False)
    successfully_parsed = models.BooleanField(verbose_name=_("Was parsed successfully?"), default=True)
    errors = models.TextField(verbose_name=_("Errors"), blank=True)
    station = models.ForeignKey(
        "stations.Station", verbose_name=_("Station"), on_delete=models.CASCADE, null=True, blank=True
    )

    class Meta:
        verbose_name = _("Telegram")
        verbose_name_plural = _("Telegrams")

    def __str__(self):
        return self.telegram if len(self.telegram) <= 30 else f"{self.telegram[:30]}..."
