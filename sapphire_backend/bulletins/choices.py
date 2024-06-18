from django.db import models
from django.utils.translation import gettext_lazy as _


class BulletinType(models.TextChoices):
    DAILY = "dl", _("Daily")
    DECADAL = "dc", _("Decadal")


class BulletinTagType(models.TextChoices):
    DATA = "d", _("Data")
    HEADER = "h", _("Header")
    GENERAL = "g", _("General")
