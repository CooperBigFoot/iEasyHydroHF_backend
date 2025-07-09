from datetime import date, timedelta

import pytest

from sapphire_backend.estimations.models import (
    EstimationsWaterLevelDailyAverage,
    EstimationsWaterLevelDailyAverageWithPeriods,
)
from sapphire_backend.utils.aggregations import custom_average
from sapphire_backend.utils.rounding import custom_ceil, custom_round


class TestHydroStationWaterDischargeDailyAverage:
    start_date = date(2020, 2, 1)
    end_date = date(2020, 2, 15)

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("water_level_metrics_daily_generator", [(start_date, end_date)], indirect=True)
    def test_water_level_daily_average(
        self,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
    ):
        wlda_estimated_queryset = EstimationsWaterLevelDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__date__range=(self.start_date, self.end_date),
        ).order_by("timestamp_local")

        wlda_estimated_list = list(wlda_estimated_queryset.values_list("avg_value", flat=True))
        for wlda_estimated, wld_pair in zip(wlda_estimated_list, water_level_metrics_daily_generator):
            wl_morning, wl_evening = wld_pair
            wlda_expected = custom_ceil(custom_average([wl_morning.avg_value, wl_evening.avg_value]))

            assert custom_round(wlda_estimated, 6) == custom_round(wlda_expected, 6)


class TestHydroStationWaterLevelDailyAverageWithPeriods:
    """Test water level daily average filtering with calculation periods."""

    start_date = date(2020, 2, 1)
    end_date = date(2020, 3, 1)

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("water_level_metrics_daily_generator", [(start_date, end_date)], indirect=True)
    def test_water_level_daily_average_with_suspended_period_excludes_data(
        self,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
        suspended_calculation_period,  # 2020-02-10 to 2020-02-15
    ):
        """Test that SUSPENDED periods exclude water level data completely."""
        # Check that data exists in the base view (without periods)
        base_wlda_count = EstimationsWaterLevelDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__date__range=(self.start_date, self.end_date),
        ).count()
        assert base_wlda_count == 30  # number of days from 2020-02-01 to 2020-03-01

        # Data within suspended period should be excluded
        suspended_period_wlda_count = EstimationsWaterLevelDailyAverageWithPeriods.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__gte=suspended_calculation_period.start_date_local,
            timestamp_local__lt=suspended_calculation_period.end_date_local,
        ).count()
        assert suspended_period_wlda_count == 0

        # Data outside suspended period should still exist
        before_suspended_wlda_count = EstimationsWaterLevelDailyAverageWithPeriods.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__lt=suspended_calculation_period.start_date_local,
        ).count()
        assert (
            before_suspended_wlda_count == 9
        )  # 9 days from 2020-02-01 to 2020-02-10 (excluded since the period starts then)

        after_suspended_wlda_count = EstimationsWaterLevelDailyAverageWithPeriods.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__gte=suspended_calculation_period.end_date_local,
        ).count()
        assert after_suspended_wlda_count == 16  # 16 days from 2020-02-15 to 2020-03-01

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("water_level_metrics_daily_generator", [(start_date, end_date)], indirect=True)
    def test_water_level_daily_average_with_privodka_period_excludes_first_day_only(
        self,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
        manual_privodka_calculation_period,  # 2020-02-20 to 2020-02-25
    ):
        """Test that MANUAL PRIVODKA periods exclude only the first day."""
        # First day should be excluded
        first_day_start = manual_privodka_calculation_period.start_date_local
        first_day_end = first_day_start + timedelta(days=1)
        first_day_wlda_count = EstimationsWaterLevelDailyAverageWithPeriods.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__gte=first_day_start,
            timestamp_local__lt=first_day_end,
        ).count()
        assert first_day_wlda_count == 0

        # Other days in the period should still exist
        second_day_start = first_day_start + timedelta(days=1)
        period_end = manual_privodka_calculation_period.end_date_local
        other_days_wlda_count = EstimationsWaterLevelDailyAverageWithPeriods.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__gte=second_day_start,
            timestamp_local__lt=period_end,
        ).count()
        assert other_days_wlda_count == 4  # 4 days from 2020-02-21 to 2020-02-24

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("water_level_metrics_daily_generator", [(start_date, end_date)], indirect=True)
    def test_water_level_daily_average_with_manual_period_allows_data_through(
        self,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
        manual_calculation_period,  # 2020-02-15 to 2020-02-20
    ):
        """Test that MANUAL periods (non-PRIVODKA) allow water level data through."""
        # Data within manual period should exist (not filtered out)
        manual_period_wlda_count = EstimationsWaterLevelDailyAverageWithPeriods.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__gte=manual_calculation_period.start_date_local,
            timestamp_local__lt=manual_calculation_period.end_date_local,
        ).count()
        assert manual_period_wlda_count == 5  # 5 days from 2020-02-15 to 2020-02-19

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("water_level_metrics_daily_generator", [(start_date, end_date)], indirect=True)
    def test_water_level_daily_average_with_inactive_period_does_not_filter(
        self,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
        suspended_calculation_period,
    ):
        """Test that inactive periods do not filter water level data."""
        # Deactivate the period
        suspended_calculation_period.is_active = False
        suspended_calculation_period.save()

        # Data within the period should exist since period is inactive
        inactive_period_wlda_count = EstimationsWaterLevelDailyAverageWithPeriods.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__gte=suspended_calculation_period.start_date_local,
            timestamp_local__lt=suspended_calculation_period.end_date_local,
        ).count()
        assert inactive_period_wlda_count == 5  # 5 days from 2020-02-15 to 2020-02-19

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("water_level_metrics_daily_generator", [(start_date, end_date)], indirect=True)
    def test_water_level_daily_average_values_match_base_view_when_no_periods(
        self,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
    ):
        """Test that values match the base view when no calculation periods are affecting the data."""
        # Use a date range outside any calculation periods
        test_start = date(2020, 1, 20)
        test_end = date(2020, 1, 30)

        base_wlda_values = list(
            EstimationsWaterLevelDailyAverage.objects.filter(
                station_id=manual_hydro_station_kyrgyz.id,
                timestamp_local__date__range=(test_start, test_end),
            )
            .order_by("timestamp_local")
            .values_list("avg_value", flat=True)
        )

        periods_wlda_values = list(
            EstimationsWaterLevelDailyAverageWithPeriods.objects.filter(
                station_id=manual_hydro_station_kyrgyz.id,
                timestamp_local__date__range=(test_start, test_end),
            )
            .order_by("timestamp_local")
            .values_list("avg_value", flat=True)
        )

        assert len(base_wlda_values) == len(periods_wlda_values)
        for base_val, periods_val in zip(base_wlda_values, periods_wlda_values):
            assert custom_round(base_val, 6) == custom_round(periods_val, 6)
