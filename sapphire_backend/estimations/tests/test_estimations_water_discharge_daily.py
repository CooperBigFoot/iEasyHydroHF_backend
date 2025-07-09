from datetime import date, timedelta

import pytest

from sapphire_backend.estimations.models import EstimationsWaterDischargeDaily
from sapphire_backend.metrics.choices import HydrologicalMeasurementType, HydrologicalMetricName, MetricUnit
from sapphire_backend.metrics.models import HydrologicalMetric
from sapphire_backend.utils.datetime_helper import DatetimeRange, SmartDatetime
from sapphire_backend.utils.rounding import custom_round


class TestHydroStationWaterDischargeDaily:
    def test_water_discharge_daily_morning(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
    ):
        timestamp = discharge_model_manual_hydro_station_kyrgyz.valid_from_local + timedelta(days=1)
        smart_dt = SmartDatetime(timestamp, station=manual_hydro_station_kyrgyz, tz_included=False)

        water_level_morning = HydrologicalMetric(
            timestamp_local=smart_dt.morning_local,
            avg_value=70,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_hydro_station_kyrgyz,
        )
        water_level_morning.save()

        discharge_morning_expected = discharge_model_manual_hydro_station_kyrgyz.estimate_discharge(
            water_level_morning.avg_value
        )

        discharge_morning_estimated = EstimationsWaterDischargeDaily.objects.get(
            station_id=manual_hydro_station_kyrgyz.id, timestamp_local=smart_dt.morning_local
        ).avg_value

        assert custom_round(discharge_morning_estimated, 6) == custom_round(discharge_morning_expected, 6)

    def test_water_discharge_daily_evening(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
    ):
        timestamp = discharge_model_manual_hydro_station_kyrgyz.valid_from_local + timedelta(days=1)
        smart_dt = SmartDatetime(timestamp, station=manual_hydro_station_kyrgyz, tz_included=False)

        water_level_evening = HydrologicalMetric(
            timestamp_local=smart_dt.evening_local,
            avg_value=135,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_hydro_station_kyrgyz,
        )
        water_level_evening.save()

        discharge_evening_expected = discharge_model_manual_hydro_station_kyrgyz.estimate_discharge(
            water_level_evening.avg_value
        )

        discharge_evening_estimated = EstimationsWaterDischargeDaily.objects.get(
            station_id=manual_hydro_station_kyrgyz.id, timestamp_local=smart_dt.evening_local
        ).avg_value

        assert custom_round(discharge_evening_estimated, 6) == custom_round(discharge_evening_expected, 6)

    def test_water_discharge_daily_different_curves_same_day(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        discharge_second_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
    ):
        # Set up the second model to be valid from the same day as the first model
        timestamp = discharge_model_manual_hydro_station_kyrgyz.valid_from_local
        discharge_second_model_manual_hydro_station_kyrgyz.valid_from_local = timestamp.replace(hour=12, minute=0)
        discharge_second_model_manual_hydro_station_kyrgyz.save()

        smart_dt = SmartDatetime(timestamp, station=manual_hydro_station_kyrgyz, tz_included=False)

        # Create morning water level measurement
        water_level_morning = HydrologicalMetric(
            timestamp_local=smart_dt.morning_local,
            avg_value=70,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_hydro_station_kyrgyz,
        )
        water_level_morning.save()

        # Create evening water level measurement
        water_level_evening = HydrologicalMetric(
            timestamp_local=smart_dt.evening_local,
            avg_value=135,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_hydro_station_kyrgyz,
        )
        water_level_evening.save()

        # Calculate expected discharge values using different curves
        discharge_morning_expected = discharge_model_manual_hydro_station_kyrgyz.estimate_discharge(
            water_level_morning.avg_value
        )
        discharge_evening_expected = discharge_second_model_manual_hydro_station_kyrgyz.estimate_discharge(
            water_level_evening.avg_value
        )

        # Get actual discharge values from the database
        discharge_morning_estimated = EstimationsWaterDischargeDaily.objects.get(
            station_id=manual_hydro_station_kyrgyz.id, timestamp_local=smart_dt.morning_local
        ).avg_value
        discharge_evening_estimated = EstimationsWaterDischargeDaily.objects.get(
            station_id=manual_hydro_station_kyrgyz.id, timestamp_local=smart_dt.evening_local
        ).avg_value

        # Verify that morning discharge uses first curve and evening uses second curve
        assert custom_round(discharge_morning_estimated, 6) == custom_round(discharge_morning_expected, 6)
        assert custom_round(discharge_evening_estimated, 6) == custom_round(discharge_evening_expected, 6)


class TestHydroStationWaterDischargeDailyMultipleRatingCurves:
    start_date = date(2020, 2, 1)
    end_date = date(2020, 4, 1)

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("water_level_metrics_daily_generator", [(start_date, end_date)], indirect=True)
    def test_water_discharge_daily_morning_two_rating_curves(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        discharge_second_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
    ):
        start_morning_local = SmartDatetime(self.start_date, station=manual_hydro_station_kyrgyz).morning_local
        end_morning_local = SmartDatetime(self.end_date, station=manual_hydro_station_kyrgyz).morning_local
        datetime_range = DatetimeRange(start_morning_local, end_morning_local, timedelta(days=1))
        wld_morning_queryset = HydrologicalMetric.objects.filter(
            station=manual_hydro_station_kyrgyz,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            timestamp_local__in=datetime_range,
        ).order_by("timestamp_local")
        curve1 = discharge_model_manual_hydro_station_kyrgyz
        curve2 = discharge_second_model_manual_hydro_station_kyrgyz
        wdd_morning_curve1 = [
            {"timestamp_local": wld.timestamp_local, "avg_value": curve1.estimate_discharge(wld.avg_value)}
            for wld in wld_morning_queryset
            if wld.timestamp_local.date() < curve2.valid_from_local.date()
        ]
        wdd_morning_curve2 = [
            {"timestamp_local": wld.timestamp_local, "avg_value": curve2.estimate_discharge(wld.avg_value)}
            for wld in wld_morning_queryset
            if wld.timestamp_local.date() >= curve2.valid_from_local.date()
        ]
        wdd_morning_expected = wdd_morning_curve1 + wdd_morning_curve2
        wdd_morning_queryset = EstimationsWaterDischargeDaily.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__in=datetime_range,
        ).order_by("timestamp_local")
        wdd_morning_estimated = wdd_morning_queryset.values("timestamp_local", "avg_value")

        assert len(wdd_morning_estimated) == len(wdd_morning_expected)
        for estimated, expected in zip(wdd_morning_estimated, wdd_morning_expected):
            assert estimated["timestamp_local"] == expected["timestamp_local"]
            assert custom_round(estimated["avg_value"], 6) == custom_round(expected["avg_value"], 6)

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("water_level_metrics_daily_generator", [(start_date, end_date)], indirect=True)
    def test_water_discharge_daily_evening_two_rating_curves(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        discharge_second_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
    ):
        start_evening_local = SmartDatetime(self.start_date, station=manual_hydro_station_kyrgyz).evening_local
        end_evening_local = SmartDatetime(self.end_date, station=manual_hydro_station_kyrgyz).evening_local
        datetime_range = DatetimeRange(start_evening_local, end_evening_local, timedelta(days=1))
        wld_evening_queryset = HydrologicalMetric.objects.filter(
            station=manual_hydro_station_kyrgyz,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            timestamp_local__in=datetime_range,
        ).order_by("timestamp_local")
        curve1 = discharge_model_manual_hydro_station_kyrgyz
        curve2 = discharge_second_model_manual_hydro_station_kyrgyz
        wdd_evening_curve1 = [
            {"timestamp_local": wld.timestamp_local, "avg_value": curve1.estimate_discharge(wld.avg_value)}
            for wld in wld_evening_queryset
            if wld.timestamp_local.date() < curve2.valid_from_local.date()
        ]
        wdd_evening_curve2 = [
            {"timestamp_local": wld.timestamp_local, "avg_value": curve2.estimate_discharge(wld.avg_value)}
            for wld in wld_evening_queryset
            if wld.timestamp_local.date() >= curve2.valid_from_local.date()
        ]

        wdd_evening_expected = wdd_evening_curve1 + wdd_evening_curve2
        wdd_evening_queryset = EstimationsWaterDischargeDaily.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__in=datetime_range,
        ).order_by("timestamp_local")
        wdd_evening_estimated = wdd_evening_queryset.values("timestamp_local", "avg_value")

        assert len(wdd_evening_estimated) == len(wdd_evening_expected)
        for estimated, expected in zip(wdd_evening_estimated, wdd_evening_expected):
            assert estimated["timestamp_local"] == expected["timestamp_local"]
            assert custom_round(estimated["avg_value"], 6) == custom_round(expected["avg_value"], 6)


class TestHydroStationWaterDischargeDailyWithCalculationPeriods:
    """Test discharge calculations with MANUAL, SUSPENDED, and PRIVODKA calculation periods."""

    def test_water_discharge_daily_with_manual_calculation_period_uses_override_values(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_calculation_period,
        regular_user_kyrgyz,
    ):
        """Test that manual calculation periods use override discharge values instead of model calculations."""
        # Use a date within the manual calculation period (2020-02-20 to 2020-02-25)
        test_date = manual_calculation_period.start_date_local + timedelta(days=1)
        smart_dt = SmartDatetime(test_date, station=manual_hydro_station_kyrgyz, tz_included=False)

        # Create water level measurement
        water_level_morning = HydrologicalMetric(
            timestamp_local=smart_dt.morning_local,
            avg_value=80,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_hydro_station_kyrgyz,
        )
        water_level_morning.save()

        # Create manual override discharge value
        manual_discharge_override = HydrologicalMetric(
            timestamp_local=smart_dt.morning_local,
            avg_value=90.5,  # Manual override value
            unit=MetricUnit.WATER_DISCHARGE,
            metric_name=HydrologicalMetricName.WATER_DISCHARGE_DAILY,
            value_type=HydrologicalMeasurementType.OVERRIDE,  # Override type
            station=manual_hydro_station_kyrgyz,
        )
        manual_discharge_override.save()

        # Get discharge from the view - should use override, not model calculation
        discharge_result = EstimationsWaterDischargeDaily.objects.get(
            station_id=manual_hydro_station_kyrgyz.id, timestamp_local=smart_dt.morning_local
        )

        # Should use the override value, not the model calculation
        assert custom_round(discharge_result.avg_value, 6) == custom_round(manual_discharge_override.avg_value, 6)
        assert discharge_result.value_type == "O"  # Override type

    def test_water_discharge_daily_without_calculation_period_uses_model_values(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
    ):
        """Test that normal periods use model calculations when no calculation period is active."""
        # Use a date outside any calculation period
        test_date = discharge_model_manual_hydro_station_kyrgyz.valid_from_local + timedelta(days=1)
        smart_dt = SmartDatetime(test_date, station=manual_hydro_station_kyrgyz, tz_included=False)

        # Create water level measurement
        water_level_morning = HydrologicalMetric(
            timestamp_local=smart_dt.morning_local,
            avg_value=80,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_hydro_station_kyrgyz,
        )
        water_level_morning.save()

        # Calculate expected discharge using the model
        expected_discharge = discharge_model_manual_hydro_station_kyrgyz.estimate_discharge(
            water_level_morning.avg_value
        )

        # Get discharge from the view - should use model calculation
        discharge_result = EstimationsWaterDischargeDaily.objects.get(
            station_id=manual_hydro_station_kyrgyz.id, timestamp_local=smart_dt.morning_local
        )

        assert custom_round(discharge_result.avg_value, 6) == custom_round(expected_discharge, 6)
        assert discharge_result.value_type == "E"  # Estimated type

    def test_water_discharge_daily_manual_privodka_excludes_first_day_only(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_privodka_calculation_period,
    ):
        """Test that MANUAL PRIVODKA periods exclude all estimated discharges, not just the first day."""
        # Test first day (should be excluded from model calculations)
        first_day = manual_privodka_calculation_period.start_date_local
        smart_dt_first = SmartDatetime(first_day, station=manual_hydro_station_kyrgyz, tz_included=False)

        # Create water level for first day
        water_level_first_day = HydrologicalMetric(
            timestamp_local=smart_dt_first.morning_local,
            avg_value=90,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_hydro_station_kyrgyz,
        )
        water_level_first_day.save()

        # Test second day (should use normal model calculations)
        second_day = manual_privodka_calculation_period.start_date_local + timedelta(days=1)
        smart_dt_second = SmartDatetime(second_day, station=manual_hydro_station_kyrgyz, tz_included=False)

        # Create water level for second day
        water_level_second_day = HydrologicalMetric(
            timestamp_local=smart_dt_second.morning_local,
            avg_value=95,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_hydro_station_kyrgyz,
        )
        water_level_second_day.save()

        # First day should not have model-calculated discharge (excluded)
        with pytest.raises(EstimationsWaterDischargeDaily.DoesNotExist):
            EstimationsWaterDischargeDaily.objects.get(
                station_id=manual_hydro_station_kyrgyz.id,
                timestamp_local=smart_dt_first.morning_local,
            )

        # Second day should also not have it because the app is expecting override values from the operator
        with pytest.raises(EstimationsWaterDischargeDaily.DoesNotExist):
            EstimationsWaterDischargeDaily.objects.get(
                station_id=manual_hydro_station_kyrgyz.id, timestamp_local=smart_dt_second.morning_local
            )

    def test_water_discharge_daily_inactive_calculation_period_does_not_affect_calculations(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        suspended_calculation_period,
    ):
        """Test that inactive calculation periods do not affect discharge calculations."""
        # Deactivate the calculation period
        suspended_calculation_period.is_active = False
        suspended_calculation_period.save()

        # Use a date within the period range but period is inactive
        test_date = suspended_calculation_period.start_date_local + timedelta(days=1)
        smart_dt = SmartDatetime(test_date, station=manual_hydro_station_kyrgyz, tz_included=False)

        # Create water level measurement
        water_level_morning = HydrologicalMetric(
            timestamp_local=smart_dt.morning_local,
            avg_value=75,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_hydro_station_kyrgyz,
        )
        water_level_morning.save()

        # Should use model calculation since period is inactive
        expected_discharge = discharge_model_manual_hydro_station_kyrgyz.estimate_discharge(
            water_level_morning.avg_value
        )

        discharge_result = EstimationsWaterDischargeDaily.objects.get(
            station_id=manual_hydro_station_kyrgyz.id, timestamp_local=smart_dt.morning_local
        )

        assert custom_round(discharge_result.avg_value, 6) == custom_round(expected_discharge, 6)
        assert discharge_result.value_type == "E"
