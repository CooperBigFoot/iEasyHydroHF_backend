import os

from django.db import models
from django.utils.translation import gettext_lazy as _


class FileState(models.Model):
    filename = models.TextField(unique=True, verbose_name=_("Original remote filename"))
    remote_path = models.TextField(verbose_name=_("File path on the remote location"))
    local_path = models.TextField(blank=True, verbose_name=_("Local file path"))
    state_timestamp = models.DateTimeField(auto_now=True, verbose_name=_("Timestamp of last state update"))
    ingester_name = models.TextField(verbose_name=_("Ingester name"))

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filename = os.path.basename(self.remote_path)

    def __str__(self):
        return self.filename
