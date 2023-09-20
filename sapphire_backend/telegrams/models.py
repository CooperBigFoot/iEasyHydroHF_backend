from django.db import models
from django.utils.translation import gettext_lazy as _

from sapphire_backend.utils.mixins.models import CreatedDateMixin


class Telegram(CreatedDateMixin, models.Model):
    telegram = models.TextField(verbose_name=_("Original telegram(s)"))
    decoded_values = models.JSONField(verbose_name=_("Decoded values"))
    automatically_ingested = models.BooleanField(verbose_name=_("Was automatically ingested?"), default=False)

    class Meta:
        verbose_name = _("Telegram")
        verbose_name_plural = _("Telegrams")
