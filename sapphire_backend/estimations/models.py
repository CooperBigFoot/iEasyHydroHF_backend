from django.db import models
from django.db.models import F, Func, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from sapphire_backend.metrics.managers import HydrologicalNormQuerySet
from sapphire_backend.metrics.mixins import BaseHydroMetricMixin, MinMaxValueMixin, NormModelMixin, SensorInfoMixin
from sapphire_backend.utils.mixins.models import CreateLastModifiedDateMixin, UUIDMixin
from sapphire_backend.utils.rounding import hydrological_round


class DischargeModel(UUIDMixin, models.Model):
    name = models.CharField(verbose_name=_("Discharge model name"), max_length=100, blank=False)
    param_a = models.DecimalField(verbose_name=_("Parameter a"), max_digits=50, decimal_places=30)
    param_b = models.DecimalField(verbose_name=_("Parameter b"), max_digits=50, decimal_places=30)
    param_c = models.DecimalField(verbose_name=_("Parameter c"), max_digits=50, decimal_places=30)
    valid_from_local = models.DateTimeField()
    station = models.ForeignKey("stations.HydrologicalStation", verbose_name=_("Station"), on_delete=models.PROTECT)

    class Meta:
        verbose_name = _("Discharge model")
        verbose_name_plural = _("Discharge models")
        ordering = ["-valid_from_local"]

    def __str__(self):
        return f"DischargeModel ({self.name}): Q = {self.param_c} (H + {self.param_a} ) ^ {self.param_b}, valid from local: {self.valid_from_local}"

    def estimate_discharge(self, water_level):
        return hydrological_round(
            float(self.param_c) * (float(water_level) + float(self.param_a)) ** float(self.param_b)
        )


class EstimationsWaterLevelDailyAverage(BaseHydroMetricMixin, MinMaxValueMixin, SensorInfoMixin, models.Model):
    station = models.ForeignKey(
        "stations.HydrologicalStation", verbose_name=_("Hydrological station"), on_delete=models.DO_NOTHING
    )

    class Meta:
        managed = False
        db_table = "estimations_water_level_daily_average"


class EstimationsWaterLevelDecadeAverage(BaseHydroMetricMixin, MinMaxValueMixin, SensorInfoMixin, models.Model):
    station = models.ForeignKey(
        "stations.HydrologicalStation", verbose_name=_("Hydrological station"), on_delete=models.DO_NOTHING
    )

    class Meta:
        managed = False
        db_table = "estimations_water_level_decade_average"


class EstimationsWaterDischargeDaily(BaseHydroMetricMixin, MinMaxValueMixin, SensorInfoMixin, models.Model):
    station = models.ForeignKey(
        "stations.HydrologicalStation", verbose_name=_("Hydrological station"), on_delete=models.DO_NOTHING
    )

    class Meta:
        managed = False
        db_table = "estimations_water_discharge_daily"


class EstimationsWaterDischargeDailyAverage(BaseHydroMetricMixin, MinMaxValueMixin, SensorInfoMixin, models.Model):
    station = models.ForeignKey(
        "stations.HydrologicalStation", verbose_name=_("Hydrological station"), on_delete=models.DO_NOTHING
    )

    class Meta:
        managed = False
        db_table = "estimations_water_discharge_daily_average"


class EstimationsWaterDischargeFivedayAverage(BaseHydroMetricMixin, MinMaxValueMixin, SensorInfoMixin, models.Model):
    station = models.ForeignKey(
        "stations.HydrologicalStation", verbose_name=_("Hydrological station"), on_delete=models.DO_NOTHING
    )

    class Meta:
        managed = False
        db_table = "estimations_water_discharge_fiveday_average"


class EstimationsWaterDischargeDecadeAverage(BaseHydroMetricMixin, MinMaxValueMixin, SensorInfoMixin, models.Model):
    station = models.ForeignKey(
        "stations.HydrologicalStation", verbose_name=_("Hydrological station"), on_delete=models.DO_NOTHING
    )

    class Meta:
        managed = False
        db_table = "estimations_water_discharge_decade_average"


class EstimationsWaterDischargeDailyVirtual(BaseHydroMetricMixin, models.Model):
    station = models.ForeignKey(
        "stations.VirtualStation", verbose_name=_("Virtual station"), on_delete=models.DO_NOTHING
    )

    class Meta:
        managed = False
        db_table = "estimations_water_discharge_daily_virtual"


class EstimationsWaterDischargeDailyAverageVirtual(BaseHydroMetricMixin, models.Model):
    station = models.ForeignKey(
        "stations.VirtualStation", verbose_name=_("Virtual station"), on_delete=models.DO_NOTHING
    )

    class Meta:
        managed = False
        db_table = "estimations_water_discharge_daily_average_virtual"


class EstimationsWaterDischargeFivedayAverageVirtual(BaseHydroMetricMixin, models.Model):
    station = models.ForeignKey(
        "stations.VirtualStation", verbose_name=_("Virtual station"), on_delete=models.DO_NOTHING
    )

    class Meta:
        managed = False
        db_table = "estimations_water_discharge_fiveday_average_virtual"


class EstimationsWaterDischargeDecadeAverageVirtual(BaseHydroMetricMixin, models.Model):
    station = models.ForeignKey(
        "stations.VirtualStation", verbose_name=_("Virtual station"), on_delete=models.DO_NOTHING
    )

    class Meta:
        managed = False
        db_table = "estimations_water_discharge_decade_average_virtual"


class EstimationsWaterTemperatureDaily(BaseHydroMetricMixin, MinMaxValueMixin, SensorInfoMixin, models.Model):
    station = models.ForeignKey(
        "stations.HydrologicalStation", verbose_name=_("Hydrological station"), on_delete=models.DO_NOTHING
    )

    class Meta:
        managed = False
        db_table = "estimations_water_temperature_daily"


class EstimationsAirTemperatureDaily(BaseHydroMetricMixin, MinMaxValueMixin, SensorInfoMixin, models.Model):
    station = models.ForeignKey(
        "stations.HydrologicalStation", verbose_name=_("Hydrological station"), on_delete=models.DO_NOTHING
    )

    class Meta:
        managed = False
        db_table = "estimations_air_temperature_daily"


class HydrologicalNormVirtual(NormModelMixin, models.Model):
    station = models.ForeignKey(
        "stations.VirtualStation",
        to_field="uuid",
        verbose_name=_("Virtual station"),
        on_delete=models.CASCADE,
    )
    objects = HydrologicalNormQuerySet.as_manager()

    class Meta:
        managed = False
        db_table = "estimations_hydrologicalnorm_virtual"


class HydrologicalRound(Func):
    function = "hydrological_round"


class DischargeCalculationPeriod(UUIDMixin, CreateLastModifiedDateMixin, models.Model):
    class CalculationState(models.TextChoices):
        MANUAL = "MANUAL", _("Manual Discharge")
        SUSPENDED = "SUSPENDED", _("No Calculation")

    class CalculationReason(models.TextChoices):
        ICE = "ICE", _("Ice Phenomena")
        PRIVODKA = "PRIVODKA", _("Privodka")
        STATION_CLOSED = "STATION_CLOSED", _("Station Closed")
        OTHER = "OTHER", _("Other")

    station = models.ForeignKey(
        "stations.HydrologicalStation",
        verbose_name=_("Station"),
        to_field="uuid",
        on_delete=models.PROTECT,
        related_name="discharge_calculation_periods",
    )

    user = models.ForeignKey(
        "users.User",
        verbose_name=_("Created By"),
        to_field="uuid",
        on_delete=models.PROTECT,
        related_name="discharge_calculation_periods",
    )

    start_date_local = models.DateTimeField(verbose_name=_("Start Date"))
    end_date_local = models.DateTimeField(verbose_name=_("End Date"), null=True, blank=True)

    state = models.CharField(verbose_name=_("Calculation State"), max_length=20, choices=CalculationState.choices)

    reason = models.CharField(verbose_name=_("Reason"), max_length=20, choices=CalculationReason.choices)

    is_active = models.BooleanField(verbose_name=_("Is Active"), default=True)

    comments = models.TextField(verbose_name=_("Comments"), blank=True)

    class Meta:
        verbose_name = _("Discharge Calculation Period")
        verbose_name_plural = _("Discharge Calculation Periods")
        ordering = ["-start_date_local"]
        constraints = [
            models.CheckConstraint(
                check=Q(end_date_local__isnull=True) | Q(end_date_local__gt=F("start_date_local")),
                name="end_date_local__after_start_date_local",
            ),
        ]

    def __str__(self):
        return f"{self.station.name} - {self.get_state_display()} ({self.start_date_local})"

    @property
    def is_current(self):
        """Return True if this period is currently active and within its date range."""
        now = timezone.now()
        return (
            self.is_active
            and self.start_date_local <= now
            and (self.end_date_local is None or self.end_date_local >= now)
        )
