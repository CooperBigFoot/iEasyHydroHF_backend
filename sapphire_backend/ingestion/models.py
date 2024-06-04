import os
from datetime import datetime
from zoneinfo import ZoneInfo

from django.db import models
from django.utils.translation import gettext_lazy as _

from sapphire_backend.utils.mixins.models import CreatedDateMixin


class FileState(models.Model):
    remote_path = models.TextField(verbose_name=_("File path on the remote location"))
    local_path = models.TextField(blank=True, null=True, verbose_name=_("Local file path"))
    state_timestamp = models.DateTimeField(verbose_name=_("Timestamp with timezone"))

    class States(models.TextChoices):
        DISCOVERED = "discovered", _("Discovered")
        DOWNLOADED = "downloaded", _("Downloaded")
        PROCESSING = "processing", _("Processing")
        PROCESSED = "processed", _("Processed")
        FAILED = "failed", _("Failed")

    state = models.CharField(
        verbose_name=_("State name"),
        choices=States,
        default=States.DISCOVERED,
        blank=False,
    )

    class Meta:
        verbose_name = _("File state")
        verbose_name_plural = _("File states")

    @property
    def filename(self):
        return os.path.basename(self.remote_path)

    def change_state(self, new_state):
        self.state = new_state
        self.state_timestamp = datetime.now(tz=ZoneInfo("UTC"))

    def __str__(self):
        return self.filename
