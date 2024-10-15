from django.db import models
from django.utils.translation import gettext_lazy as _

from sapphire_backend.ingestion.models import FileState
from sapphire_backend.users.models import User
from sapphire_backend.utils.mixins.models import CreatedDateMixin


class TelegramReceived(CreatedDateMixin, models.Model):
    telegram = models.TextField(verbose_name=_("Received telegram(s)"))
    valid = models.BooleanField(verbose_name=_("Is telegram valid?"), default=True)
    station_code = models.CharField(verbose_name=_("Station code"), max_length=100, blank=True)
    decoded_values = models.JSONField(verbose_name=_("Decoded values"), blank=True, null=True)
    errors = models.TextField(verbose_name=_("Errors"), blank=True)
    acknowledged = models.BooleanField(default=False)
    acknowledged_ts = models.DateTimeField(null=True, blank=True, verbose_name=_("Acknowledged timestamp"))
    acknowledged_by = models.ForeignKey(User, to_field="id", on_delete=models.SET_NULL, null=True, blank=True)
    filestate = models.ForeignKey(FileState, to_field="id", on_delete=models.SET_NULL, null=True, blank=True)
    auto_stored = models.BooleanField(verbose_name=_("Was telegram automatically stored?"), default=False)
    organization = models.ForeignKey(
        "organizations.Organization",
        to_field="id",
        verbose_name=_("Organization"),
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name = _("Telegram received")
        verbose_name_plural = _("Telegrams received")


class TelegramStored(CreatedDateMixin, models.Model):
    telegram = models.TextField(verbose_name=_("Stored telegram(s)"))
    telegram_day = models.DateField(verbose_name=_("Telegram day"))
    station_code = models.CharField(verbose_name=_("Station code"), max_length=100, blank=False)
    auto_stored = models.BooleanField(verbose_name=_("Was telegram automatically stored?"), default=False)
    stored_by = models.ForeignKey(User, to_field="id", on_delete=models.SET_NULL, null=True, blank=True)
    organization = models.ForeignKey(
        "organizations.Organization",
        to_field="id",
        verbose_name=_("Organization"),
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name = _("Telegram stored")
        verbose_name_plural = _("Telegrams stored")


class TelegramParserLog(CreatedDateMixin, models.Model):
    telegram = models.TextField(verbose_name=_("Original telegram"))
    station_code = models.CharField(verbose_name=_("Station code"), max_length=100, blank=True)
    decoded_values = models.JSONField(verbose_name=_("Decoded values"), blank=True, null=True)
    valid = models.BooleanField(verbose_name=_("Is telegram valid?"), default=True)
    errors = models.TextField(verbose_name=_("Errors"), blank=True)
    user = models.ForeignKey(User, to_field="id", on_delete=models.SET_NULL, null=True, blank=True)
    organization = models.ForeignKey(
        "organizations.Organization",
        verbose_name=_("Organization"),
        to_field="id",
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name = _("Telegram parser log")
        verbose_name_plural = _("Telegram parser logs")

    def __str__(self):
        return self.telegram if len(self.telegram) <= 30 else f"{self.telegram[:30]}..."
