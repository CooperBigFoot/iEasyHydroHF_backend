from datetime import date, timedelta

import pytest

from sapphire_backend.estimations.models import (
    EstimationsWaterDischargeDailyAverage,
    EstimationsWaterLevelDailyAverage,
)
from sapphire_backend.metrics.choices import HydrologicalMeasurementType, HydrologicalMetricName, MetricUnit
from sapphire_backend.metrics.models import HydrologicalMetric
from sapphire_backend.utils.datetime_helper import SmartDatetime
from sapphire_backend.utils.rounding import custom_round


class TestHydroStationWaterDischargeDailyAverageMultipleRatingCurves:
    start_date = date(2020, 2, 1)
    end_date = date(2020, 4, 1)

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("water_level_metrics_daily_generator", [(start_date, end_date)], indirect=True)
    def test_water_discharge_daily_average_two_rating_curves(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        discharge_second_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
    ):
        wlda_queryset = EstimationsWaterLevelDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__date__range=(self.start_date, self.end_date),
        ).order_by("timestamp_local")

        curve1 = discharge_model_manual_hydro_station_kyrgyz
        curve2 = discharge_second_model_manual_hydro_station_kyrgyz
        wdda_curve1 = [
            {"timestamp_local": wlda.timestamp_local, "avg_value": curve1.estimate_discharge(wlda.avg_value)}
            for wlda in wlda_queryset
            if wlda.timestamp_local.date() < curve2.valid_from_local.date()
        ]
        wdda_curve2 = [
            {"timestamp_local": wlda.timestamp_local, "avg_value": curve2.estimate_discharge(wlda.avg_value)}
            for wlda in wlda_queryset
            if wlda.timestamp_local.date() >= curve2.valid_from_local.date()
        ]

        wdda_expected = wdda_curve1 + wdda_curve2
        wdda_queryset = EstimationsWaterDischargeDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__date__range=(self.start_date, self.end_date),
        ).order_by("timestamp_local")
        wdda_estimated = wdda_queryset.values("timestamp_local", "avg_value")

        assert len(wdda_estimated) == len(wdda_expected)
        for estimated, expected in zip(wdda_estimated, wdda_expected):
            assert estimated["timestamp_local"] == expected["timestamp_local"]
            assert custom_round(estimated["avg_value"], 6) == custom_round(expected["avg_value"], 6)


class TestHydroStationWaterDischargeDailyAverageWithCalculationPeriods:
    """Test discharge daily average calculations with calculation periods."""

    start_date = date(2020, 2, 1)
    end_date = date(2020, 3, 1)

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("water_level_metrics_daily_generator", [(start_date, end_date)], indirect=True)
    def test_water_discharge_daily_average_with_suspended_period_excludes_data(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
        suspended_calculation_period,  # 2020-02-10T00:00:00Z to 2020-02-15T00:00:00Z
    ):
        """Test that SUSPENDED periods exclude discharge daily averages completely."""
        suspended_period_wdda_count = EstimationsWaterDischargeDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__gte=suspended_calculation_period.start_date_local,
            timestamp_local__lt=suspended_calculation_period.end_date_local,
        ).count()

        assert suspended_period_wdda_count == 0

        # Data outside suspended period should still exist
        before_suspended_wdda_count = EstimationsWaterDischargeDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__lt=suspended_calculation_period.start_date_local,
        ).count()
        assert before_suspended_wdda_count == 9  # 9 days

        after_suspended_wdda_count = EstimationsWaterDischargeDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__gte=suspended_calculation_period.end_date_local,
        ).count()
        assert after_suspended_wdda_count == 16  # 16 days (15 in February, 1 in March)

    @pytest.mark.django_db(transaction=True)
    def test_water_discharge_daily_average_with_manual_overrides_prioritizes_overrides(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_calculation_period,  # 2020-02-15T00:00:00Z to 2020-02-20T00:00:00Z
    ):
        """Test that manual calculation periods prioritize override values in daily averages."""
        # Use a date within the manual calculation period
        test_date = manual_calculation_period.start_date_local.date() + timedelta(days=1)  # 2020-02-16
        smart_dt = SmartDatetime(test_date, station=manual_hydro_station_kyrgyz, tz_included=False)

        # Create water level measurements
        water_level_morning = HydrologicalMetric(
            timestamp_local=smart_dt.morning_local,
            avg_value=80,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_hydro_station_kyrgyz,
        )
        water_level_morning.save()

        water_level_evening = HydrologicalMetric(
            timestamp_local=smart_dt.evening_local,
            avg_value=85,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_hydro_station_kyrgyz,
        )
        water_level_evening.save()

        # Create manual override discharge values (2 required for average)
        manual_discharge_morning = HydrologicalMetric(
            timestamp_local=smart_dt.morning_local,
            avg_value=120.5,  # Manual override value
            unit=MetricUnit.WATER_DISCHARGE,
            metric_name=HydrologicalMetricName.WATER_DISCHARGE_DAILY,
            value_type=HydrologicalMeasurementType.OVERRIDE,
            station=manual_hydro_station_kyrgyz,
        )
        manual_discharge_morning.save()

        manual_discharge_evening = HydrologicalMetric(
            timestamp_local=smart_dt.evening_local,
            avg_value=125.5,  # Manual override value
            unit=MetricUnit.WATER_DISCHARGE,
            metric_name=HydrologicalMetricName.WATER_DISCHARGE_DAILY,
            value_type=HydrologicalMeasurementType.OVERRIDE,
            station=manual_hydro_station_kyrgyz,
        )
        manual_discharge_evening.save()

        # Check that daily average uses override values
        expected_average = (manual_discharge_morning.avg_value + manual_discharge_evening.avg_value) / 2

        daily_average_result = EstimationsWaterDischargeDailyAverage.objects.get(
            station_id=manual_hydro_station_kyrgyz.id, timestamp_local__date=test_date
        )

        assert custom_round(daily_average_result.avg_value, 6) == custom_round(expected_average, 6)

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("water_level_metrics_daily_generator", [(start_date, end_date)], indirect=True)
    def test_privodka_period_without_overrides_excludes_subsequent_days(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
        manual_privodka_calculation_period,  # 2020-02-20T00:00:00Z to 2020-02-25T00:00:00Z
    ):
        """Test that MANUAL PRIVODKA periods exclude ALL days when no manual override values exist."""

        # First day should be excluded from daily averages (always excluded for PRIVODKA periods)
        first_day_wdda_count = EstimationsWaterDischargeDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__date=manual_privodka_calculation_period.start_date_local.date(),
        ).count()
        assert first_day_wdda_count == 0

        # Subsequent days should also be excluded since no manual override values exist
        subsequent_days_wdda_count = EstimationsWaterDischargeDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__gte=manual_privodka_calculation_period.start_date_local + timedelta(days=1),
            timestamp_local__lt=manual_privodka_calculation_period.end_date_local,
        ).count()
        assert subsequent_days_wdda_count == 0

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("water_level_metrics_daily_generator", [(start_date, end_date)], indirect=True)
    def test_privodka_period_with_overrides_includes_subsequent_days(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
        manual_privodka_calculation_period,  # 2020-02-20T00:00:00Z to 2020-02-25T00:00:00Z
    ):
        """Test that MANUAL PRIVODKA periods include subsequent days when manual override values exist."""

        # Create manual override discharge values for subsequent days (days 2-5 of the period)
        period_start = manual_privodka_calculation_period.start_date_local
        period_end = manual_privodka_calculation_period.end_date_local

        override_values_created = []
        for day_offset in range(1, 5):  # Days 2-5 of the period
            test_date = (period_start + timedelta(days=day_offset)).date()
            if period_start + timedelta(days=day_offset) >= period_end:
                break  # Don't create values outside the period

            smart_dt = SmartDatetime(test_date, station=manual_hydro_station_kyrgyz, tz_included=False)

            # Create two manual override values for the day (morning and evening)
            manual_discharge_morning = HydrologicalMetric(
                timestamp_local=smart_dt.morning_local,
                avg_value=100.0 + day_offset * 5,  # Different values for each day
                unit=MetricUnit.WATER_DISCHARGE,
                metric_name=HydrologicalMetricName.WATER_DISCHARGE_DAILY,
                value_type=HydrologicalMeasurementType.OVERRIDE,
                station=manual_hydro_station_kyrgyz,
            )
            manual_discharge_morning.save()

            manual_discharge_evening = HydrologicalMetric(
                timestamp_local=smart_dt.evening_local,
                avg_value=105.0 + day_offset * 5,  # Different values for each day
                unit=MetricUnit.WATER_DISCHARGE,
                metric_name=HydrologicalMetricName.WATER_DISCHARGE_DAILY,
                value_type=HydrologicalMeasurementType.OVERRIDE,
                station=manual_hydro_station_kyrgyz,
            )
            manual_discharge_evening.save()

            override_values_created.append(test_date)

        # First day should still be excluded from daily averages
        first_day_wdda_count = EstimationsWaterDischargeDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__date=manual_privodka_calculation_period.start_date_local.date(),
        ).count()
        assert first_day_wdda_count == 0

        # Subsequent days with manual overrides should have daily averages
        subsequent_days_wdda = EstimationsWaterDischargeDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__gte=manual_privodka_calculation_period.start_date_local + timedelta(days=1),
            timestamp_local__lt=manual_privodka_calculation_period.end_date_local,
        )

        subsequent_days_wdda_count = subsequent_days_wdda.count()

        assert subsequent_days_wdda_count == len(override_values_created)

        # Verify that the daily averages match the expected values from manual overrides
        for daily_avg in subsequent_days_wdda:
            test_date = daily_avg.timestamp_local.date()
            day_offset = (daily_avg.timestamp_local.date() - period_start.date()).days
            expected_avg = (100.0 + day_offset * 5 + 105.0 + day_offset * 5) / 2  # Average of morning and evening
            assert custom_round(daily_avg.avg_value, 6) == custom_round(expected_avg, 6)

    @pytest.mark.django_db(transaction=True)
    def test_water_discharge_daily_average_computed_vs_model_logic(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        discharge_second_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
    ):
        """Test the complex prioritization logic for daily averages with multiple models."""
        # Set up second model to be valid from mid-day to create multiple model scenario
        test_date = discharge_model_manual_hydro_station_kyrgyz.valid_from_local.date() + timedelta(days=1)
        discharge_second_model_manual_hydro_station_kyrgyz.valid_from_local = (
            discharge_model_manual_hydro_station_kyrgyz.valid_from_local.replace(hour=12, minute=0) + timedelta(days=1)
        )
        discharge_second_model_manual_hydro_station_kyrgyz.save()

        smart_dt = SmartDatetime(test_date, station=manual_hydro_station_kyrgyz, tz_included=False)

        # Create water level measurements that will result in different model calculations
        water_level_morning = HydrologicalMetric(
            timestamp_local=smart_dt.morning_local,
            avg_value=90,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_hydro_station_kyrgyz,
        )
        water_level_morning.save()

        water_level_evening = HydrologicalMetric(
            timestamp_local=smart_dt.evening_local,
            avg_value=95,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_hydro_station_kyrgyz,
        )
        water_level_evening.save()

        # Calculate expected values for each model
        morning_discharge = discharge_model_manual_hydro_station_kyrgyz.estimate_discharge(
            water_level_morning.avg_value
        )
        evening_discharge = discharge_second_model_manual_hydro_station_kyrgyz.estimate_discharge(
            water_level_evening.avg_value
        )

        # The view should use computed average (true mean) of the two different model results
        expected_computed_average = (morning_discharge + evening_discharge) / 2

        daily_average_result = EstimationsWaterDischargeDailyAverage.objects.get(
            station_id=manual_hydro_station_kyrgyz.id, timestamp_local__date=test_date
        )

        assert custom_round(daily_average_result.avg_value, 6) == custom_round(expected_computed_average, 6)

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("water_level_metrics_daily_generator", [(start_date, end_date)], indirect=True)
    def test_water_discharge_daily_average_inactive_period_does_not_affect_calculations(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
        suspended_calculation_period,
    ):
        """Test that inactive calculation periods do not affect daily average calculations."""
        # Deactivate the period
        suspended_calculation_period.is_active = False
        suspended_calculation_period.save()

        # Data within the inactive period should exist in daily averages
        inactive_period_wdda_count = EstimationsWaterDischargeDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__gte=suspended_calculation_period.start_date_local,
            timestamp_local__lt=suspended_calculation_period.end_date_local,
        ).count()
        assert inactive_period_wdda_count > 0
