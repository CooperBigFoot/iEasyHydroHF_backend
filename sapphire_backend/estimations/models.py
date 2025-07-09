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


class EstimationsWaterLevelDailyAverageWithPeriods(
    BaseHydroMetricMixin, MinMaxValueMixin, SensorInfoMixin, models.Model
):
    station = models.ForeignKey(
        "stations.HydrologicalStation", verbose_name=_("Hydrological station"), on_delete=models.DO_NOTHING
    )

    class Meta:
        managed = False
        db_table = "estimations_water_level_daily_average_with_periods"


class EstimationsWaterLevelDecadeAverage(BaseHydroMetricMixin, MinMaxValueMixin, SensorInfoMixin, models.Model):
    station = models.ForeignKey(
        "stations.HydrologicalStation", verbose_name=_("Hydrological station"), on_delete=models.DO_NOTHING
    )

    class Meta:
        managed = False
        db_table = "estimations_water_level_decade_average"


class EstimationsWaterDischargeDailyModel(BaseHydroMetricMixin, MinMaxValueMixin, SensorInfoMixin, models.Model):
    station = models.ForeignKey(
        "stations.HydrologicalStation", verbose_name=_("Hydrological station"), on_delete=models.DO_NOTHING
    )
    model_id = models.IntegerField(verbose_name=_("Model ID"))

    class Meta:
        managed = False
        db_table = "estimations_water_discharge_daily_model"


class EstimationsWaterDischargeDailyOverrides(BaseHydroMetricMixin, MinMaxValueMixin, SensorInfoMixin, models.Model):
    station = models.ForeignKey(
        "stations.HydrologicalStation", verbose_name=_("Hydrological station"), on_delete=models.DO_NOTHING
    )
    model_id = models.IntegerField(verbose_name=_("Model ID"))

    class Meta:
        managed = False
        db_table = "estimations_water_discharge_daily_overrides"


class EstimationsWaterDischargeDaily(BaseHydroMetricMixin, MinMaxValueMixin, SensorInfoMixin, models.Model):
    station = models.ForeignKey(
        "stations.HydrologicalStation", verbose_name=_("Hydrological station"), on_delete=models.DO_NOTHING
    )

    class Meta:
        managed = False
        db_table = "estimations_water_discharge_daily"


class EstimationsWaterDischargeDailyAverageModel(
    BaseHydroMetricMixin, MinMaxValueMixin, SensorInfoMixin, models.Model
):
    station = models.ForeignKey(
        "stations.HydrologicalStation", verbose_name=_("Hydrological station"), on_delete=models.DO_NOTHING
    )

    class Meta:
        managed = False
        db_table = "estimations_water_discharge_daily_average_model"


class EstimationsWaterDischargeDailyAverageComputed(
    BaseHydroMetricMixin, MinMaxValueMixin, SensorInfoMixin, models.Model
):
    station = models.ForeignKey(
        "stations.HydrologicalStation", verbose_name=_("Hydrological station"), on_delete=models.DO_NOTHING
    )

    class Meta:
        managed = False
        db_table = "estimations_water_discharge_daily_average_computed"


class EstimationsWaterDischargeDailyAverageOverrides(
    BaseHydroMetricMixin, MinMaxValueMixin, SensorInfoMixin, models.Model
):
    station = models.ForeignKey(
        "stations.HydrologicalStation", verbose_name=_("Hydrological station"), on_delete=models.DO_NOTHING
    )

    class Meta:
        managed = False
        db_table = "estimations_water_discharge_daily_average_overrides"


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

    comment = models.TextField(verbose_name=_("Comment"), blank=True)

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
    def is_expired(self):
        """Return True if this period is expired."""
        now = timezone.now()
        return self.end_date_local and self.end_date_local < now

    @property
    def is_current(self):
        """Return True if this period is currently active and within its date range."""
        now = timezone.now()
        return self.is_active and self.start_date_local <= now and not self.is_expired

    @classmethod
    def get_active_period(cls, station_id, timestamp=None):
        """
        Get the active calculation period for a station at a specific timestamp.

        Args:
            station_id: The ID of the hydrological station
            timestamp: The timestamp to check (defaults to current time)

        Returns:
            The active DischargeCalculationPeriod or None if no active period exists
        """
        if timestamp is None:
            timestamp = timezone.now()

        return (
            cls.objects.filter(
                station_id=station_id,
                is_active=True,
                start_date_local__lte=timestamp,
            )
            .filter(Q(end_date_local__isnull=True) | Q(end_date_local__gte=timestamp))
            .order_by("-start_date_local")
            .first()
        )

    @classmethod
    def is_manual_calculation(cls, station_id, timestamp=None):
        """
        Determine if discharge values should be manually calculated for a station at a specific timestamp.

        Args:
            station_id: The ID of the hydrological station
            timestamp: The timestamp to check (defaults to current time)

        Returns:
            bool: True if manual calculation should be used, False otherwise
        """
        period = cls.get_active_period(station_id, timestamp)

        if not period:
            return False

        return period.state == cls.CalculationState.MANUAL

    @classmethod
    def has_overlapping_period(cls, station_id, start_date, end_date=None, exclude_uuid=None):
        """
        Check if there are any overlapping periods for a given station and date range.

        This method detects the following overlap scenarios:

        1. A new period starting during an existing period
           Example:
           - Existing: Jan 1, 2023 to Mar 31, 2023
           - New: Feb 15, 2023 to Apr 30, 2023
           (The new period starts during the existing period)

        2. A new period ending during an existing period
           Example:
           - Existing: Mar 1, 2023 to May 31, 2023
           - New: Jan 1, 2023 to Apr 15, 2023
           (The new period ends during the existing period)

        3. A new period completely containing an existing period
           Example:
           - Existing: Mar 1, 2023 to Apr 30, 2023
           - New: Jan 1, 2023 to Jun 30, 2023
           (The new period completely contains the existing period)

        4. Open-ended periods (with null end_date)
           Examples:
           a) New open-ended period overlapping with existing period:
              - Existing: Jan 1, 2023 to Mar 31, 2023
              - New: Feb 15, 2023 to null (open-ended)
           b) New period overlapping with existing open-ended period:
              - Existing: Jan 1, 2023 to null (open-ended)
              - New: Mar 1, 2023 to May 31, 2023
           c) New open-ended period containing existing period:
              - Existing: Mar 1, 2023 to Apr 30, 2023
              - New: Jan 1, 2023 to null (open-ended)

        Args:
            station_id: The ID of the hydrological station
            start_date: The start date of the period to check
            end_date: The end date of the period to check (can be None for open-ended periods)
            exclude_uuid: UUID of a period to exclude from the check (useful for updates)

        Returns:
            bool: True if there are overlapping periods, False otherwise
        """
        # Base query for the station
        query = cls.objects.filter(station_id=station_id)

        # Exclude a specific period if provided (useful for updates)
        if exclude_uuid:
            query = query.exclude(uuid=exclude_uuid)

        # Case 1: New period starts during an existing period
        # (existing.start <= new.start < existing.end OR existing.end is NULL)
        case1 = query.filter(
            start_date_local__lte=start_date,
        ).filter(Q(end_date_local__isnull=True) | Q(end_date_local__gt=start_date))

        # Case 2: New period ends during an existing period
        # (existing.start < new.end <= existing.end OR existing.end is NULL)
        if end_date:
            case2 = query.filter(
                start_date_local__lt=end_date,
            ).filter(Q(end_date_local__isnull=True) | Q(end_date_local__gte=end_date))
        else:
            # If new period has no end date, check if it overlaps with any existing period
            case2 = query.filter(Q(end_date_local__isnull=True) | Q(end_date_local__gt=start_date))

        # Case 3: New period completely contains an existing period
        # (new.start <= existing.start AND (new.end >= existing.end OR new.end is NULL))
        if end_date:
            case3 = query.filter(
                start_date_local__gte=start_date,
            ).filter(Q(end_date_local__isnull=True) | Q(end_date_local__lte=end_date))
        else:
            # If new period has no end date, it will contain any period that starts after its start date
            case3 = query.filter(start_date_local__gte=start_date)

        # Combine all cases
        overlapping = case1.union(case2).union(case3)

        return overlapping.exists()
