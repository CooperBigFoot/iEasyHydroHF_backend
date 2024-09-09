from django.db import models
from django.utils.translation import gettext_lazy as _


class HistoryLogEntryType(models.TextChoices):
    USER = "U", _("User")
    TELEGRAM = "T", _("Telegram")
    INGESTER = "I", _("Ingester")
