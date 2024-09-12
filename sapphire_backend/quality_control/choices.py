from django.db import models
from django.utils.translation import gettext_lazy as _


class HistoryLogStationType(models.TextChoices):
    HYDRO = "H", _("Hydro")
    METEO = "M", _("Meteo")
