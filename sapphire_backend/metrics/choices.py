from django.db import models
from django.utils.translation import gettext_lazy as _


class HydrologicalMeasurementType(models.TextChoices):
    MANUAL = "M", _("Manual")
    AUTOMATIC = "A", _("Automatic")
    ESTIMATED = "E", _("Estimated")
    IMPORTED = "I", _("Imported")
    UNKNOWN = "U", _("Unknown")


class HydrologicalMetricName(models.TextChoices):
    WATER_LEVEL_DAILY = "WLD", _("Water level daily")
    WATER_LEVEL_DAILY_AVERAGE = "WLDA", _("Water level daily average")
    WATER_LEVEL_DECADAL = "WLDC", _("Water level decadal")

    WATER_DISCHARGE_DAILY = "WDD", _("Water discharge daily")
    WATER_DISCHARGE_DAILY_AVERAGE = "WDDA", _("Water discharge daily average")
    WATER_DISCHARGE_FIVEDAY_AVERAGE = "WDFA", _("Water discharge fiveday average")
    WATER_DISCHARGE_DECADE_AVERAGE = "WDDCA", _("Water discharge decade average")
    WATER_DISCHARGE_DECADE_AVERAGE_HISTORICAL = "WDDCAH", _("Water discharge decade average historical")

    WATER_TEMPERATURE = "WTO", _("Water temperature observation")
    AIR_TEMPERATURE = "ATO", _("Air temperature observation")
    ICE_PHENOMENA_OBSERVATION = "IPO", _("Ice phenomena observation")

    RIVER_CROSS_SECTION_AREA = "RCSA", _("River cross section area")
    MAXIMUM_DEPTH = "MD", _("Maximum depth")


class MeteorologicalMeasurementType(models.TextChoices):
    IMPORTED = "I", _("Imported")
    UNKNOWN = "U", _("Unknown")
    MANUAL = "M", _("Manual")


class MeteorologicalMetricName(models.TextChoices):
    AIR_TEMPERATURE_DECADE_AVERAGE = "ATDCA", _("Air temperature decade average")  # 0016
    AIR_TEMPERATURE_MONTH_AVERAGE = "ATMA", _("Air temperature month average")  # 0017
    PRECIPITATION_DECADE_AVERAGE = "PDCA", _("Precipitation decade average")  # 0018
    PRECIPITATION_MONTH_AVERAGE = "PMA", _("Precipitation month average")  # 0019


class MetricUnit(models.TextChoices):
    WATER_LEVEL = "cm", _("centimeter")  # '0001'
    WATER_DISCHARGE = "m^3/s", _("cubic meters per second")  # '0005'
    TEMPERATURE = "degC", _("degree celsius")  # '0013'
    ICE_PHENOMENA_OBSERVATION = "dimensionless", _("dimensionless")  # '0011'
    AREA = "m^2", _("square meter")  # '0006'
    PRECIPITATION = "mm/day", _("millimeters per day")  # 0018
