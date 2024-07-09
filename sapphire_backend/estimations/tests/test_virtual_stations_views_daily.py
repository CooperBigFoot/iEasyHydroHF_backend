from datetime import timedelta
from decimal import Decimal

import pytest

from sapphire_backend.estimations.models import (
    EstimationsWaterDischargeDaily,
    EstimationsWaterDischargeDailyAverageVirtual,
    EstimationsWaterDischargeDailyVirtual,
    EstimationsWaterLevelDailyAverage,
)
from sapphire_backend.metrics.choices import HydrologicalMeasurementType, HydrologicalMetricName, MetricUnit
from sapphire_backend.metrics.models import HydrologicalMetric
from sapphire_backend.utils.datetime_helper import SmartDatetime
from sapphire_backend.utils.db_helper import refresh_continuous_aggregate
from sapphire_backend.utils.rounding import custom_round, hydrological_round


class TestVirtualStationWaterDischargeDailyMetrics:
    def test_water_discharge_daily_morning(
        self,
        organization,
        virtual_station,
        virtual_station_association_one,
        virtual_station_association_two,
        discharge_model_manual_hydro_station_kyrgyz,
        discharge_model_manual_second_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
    ):
        timestamp = discharge_model_manual_hydro_station_kyrgyz.valid_from_local + timedelta(days=1)
        smart_dt = SmartDatetime(timestamp, station=manual_hydro_station_kyrgyz, tz_included=False)

        water_level_morning_station1 = HydrologicalMetric(
            timestamp_local=smart_dt.morning_local,
            avg_value=70,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_hydro_station_kyrgyz,
        )
        water_level_morning_station1.save()

        water_level_morning_station2 = HydrologicalMetric(
            timestamp_local=smart_dt.morning_local,
            avg_value=100,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_second_hydro_station_kyrgyz,
        )
        water_level_morning_station2.save()

        discharge_morning_station1 = EstimationsWaterDischargeDaily.objects.get(
            station_id=manual_hydro_station_kyrgyz.id, timestamp_local=smart_dt.morning_local
        ).avg_value

        discharge_morning_station2 = EstimationsWaterDischargeDaily.objects.get(
            station_id=manual_second_hydro_station_kyrgyz.id, timestamp_local=smart_dt.morning_local
        ).avg_value

        virtual_discharge_morning_expected = hydrological_round(
            virtual_station_association_one.weight / Decimal(100) * discharge_morning_station1
            + virtual_station_association_two.weight / Decimal(100) * discharge_morning_station2
        )

        virtual_discharge_morning_estimated = EstimationsWaterDischargeDailyVirtual.objects.get(
            station=virtual_station,
            timestamp_local=smart_dt.morning_local,
        ).avg_value

        assert custom_round(virtual_discharge_morning_estimated, 6) == custom_round(
            virtual_discharge_morning_expected, 6
        )

    def test_water_discharge_daily_morning_three_virtual_associations(
        self,
        organization,
        virtual_station,
        virtual_station_association_one,
        virtual_station_association_two,
        virtual_station_association_three,
        discharge_model_manual_hydro_station_kyrgyz,
        discharge_model_manual_second_hydro_station_kyrgyz,  # needed indirectly
        discharge_model_manual_third_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_third_hydro_station_kyrgyz,
    ):
        timestamp = discharge_model_manual_hydro_station_kyrgyz.valid_from_local + timedelta(days=1)
        smart_dt = SmartDatetime(timestamp, station=manual_hydro_station_kyrgyz, tz_included=False)

        water_level_morning_station1 = HydrologicalMetric(
            timestamp_local=smart_dt.morning_local,
            avg_value=70,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_hydro_station_kyrgyz,
        )
        water_level_morning_station1.save()

        water_level_morning_station2 = HydrologicalMetric(
            timestamp_local=smart_dt.morning_local,
            avg_value=100,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_second_hydro_station_kyrgyz,
        )
        water_level_morning_station2.save()

        water_level_morning_station3 = HydrologicalMetric(
            timestamp_local=smart_dt.morning_local,
            avg_value=60,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_third_hydro_station_kyrgyz,
        )
        water_level_morning_station3.save()

        discharge_morning_station1 = EstimationsWaterDischargeDaily.objects.get(
            station=manual_hydro_station_kyrgyz,
            timestamp_local=smart_dt.morning_local,
        ).avg_value

        discharge_morning_station2 = EstimationsWaterDischargeDaily.objects.get(
            station=manual_second_hydro_station_kyrgyz,
            timestamp_local=smart_dt.morning_local,
        ).avg_value
        discharge_morning_station3 = EstimationsWaterDischargeDaily.objects.get(
            station=manual_third_hydro_station_kyrgyz,
            timestamp_local=smart_dt.morning_local,
        ).avg_value
        virtual_discharge_morning_expected = hydrological_round(
            virtual_station_association_one.weight / Decimal(100) * discharge_morning_station1
            + virtual_station_association_two.weight / Decimal(100) * discharge_morning_station2
            + virtual_station_association_three.weight / Decimal(100) * discharge_morning_station3
        )

        virtual_discharge_morning_estimated = EstimationsWaterDischargeDailyVirtual.objects.get(
            station=virtual_station,
            timestamp_local=smart_dt.morning_local,
        ).avg_value

        assert custom_round(virtual_discharge_morning_estimated, 6) == custom_round(
            virtual_discharge_morning_expected, 6
        )

    def test_water_discharge_daily_evening(
        self,
        organization,
        virtual_station,
        virtual_station_association_one,
        virtual_station_association_two,
        discharge_model_manual_hydro_station_kyrgyz,
        discharge_model_manual_second_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
    ):
        timestamp = discharge_model_manual_hydro_station_kyrgyz.valid_from_local + timedelta(days=1)
        smart_dt = SmartDatetime(timestamp, station=manual_hydro_station_kyrgyz, tz_included=False)

        water_level_evening_station1 = HydrologicalMetric(
            timestamp_local=smart_dt.evening_local,
            avg_value=120,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_hydro_station_kyrgyz,
        )
        water_level_evening_station1.save()

        water_level_evening_station2 = HydrologicalMetric(
            timestamp_local=smart_dt.evening_local,
            avg_value=150,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_second_hydro_station_kyrgyz,
        )
        water_level_evening_station2.save()

        discharge_evening_station1 = EstimationsWaterDischargeDaily.objects.get(
            station=manual_hydro_station_kyrgyz, timestamp_local=smart_dt.evening_local
        ).avg_value

        discharge_evening_station2 = EstimationsWaterDischargeDaily.objects.get(
            station=manual_second_hydro_station_kyrgyz, timestamp_local=smart_dt.evening_local
        ).avg_value
        virtual_discharge_evening_expected = hydrological_round(
            virtual_station_association_one.weight / Decimal(100) * discharge_evening_station1
            + virtual_station_association_two.weight / Decimal(100) * discharge_evening_station2
        )

        virtual_discharge_evening_estimated = EstimationsWaterDischargeDailyVirtual.objects.get(
            station=virtual_station, timestamp_local=smart_dt.evening_local
        ).avg_value

        assert custom_round(virtual_discharge_evening_estimated, 6) == custom_round(
            virtual_discharge_evening_expected, 6
        )

    @pytest.mark.django_db(transaction=True)
    def test_water_discharge_daily_average(
        self,
        organization,
        virtual_station,
        virtual_station_association_one,
        virtual_station_association_two,
        discharge_model_manual_hydro_station_kyrgyz,
        discharge_model_manual_second_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
    ):
        timestamp = discharge_model_manual_hydro_station_kyrgyz.valid_from_local + timedelta(days=1)
        smart_dt = SmartDatetime(timestamp, station=manual_hydro_station_kyrgyz, tz_included=False)

        water_level_morning_station1 = HydrologicalMetric(
            timestamp_local=smart_dt.morning_local,
            avg_value=70,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_hydro_station_kyrgyz,
        )
        water_level_morning_station1.save()

        water_level_evening_station1 = HydrologicalMetric(
            timestamp_local=smart_dt.evening_local,
            avg_value=120,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_hydro_station_kyrgyz,
        )
        water_level_evening_station1.save()

        water_level_morning_station2 = HydrologicalMetric(
            timestamp_local=smart_dt.morning_local,
            avg_value=200,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_second_hydro_station_kyrgyz,
        )
        water_level_morning_station2.save()

        water_level_evening_station2 = HydrologicalMetric(
            timestamp_local=smart_dt.evening_local,
            avg_value=250,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_second_hydro_station_kyrgyz,
        )
        water_level_evening_station2.save()

        refresh_continuous_aggregate()

        water_level_average_station1 = EstimationsWaterLevelDailyAverage.objects.get(
            station=manual_hydro_station_kyrgyz, timestamp_local__date=smart_dt.local.date()
        ).avg_value

        discharge_average_station1_expected = discharge_model_manual_hydro_station_kyrgyz.estimate_discharge(
            water_level_average_station1
        )

        water_level_average_station2 = EstimationsWaterLevelDailyAverage.objects.get(
            station=manual_second_hydro_station_kyrgyz, timestamp_local__date=smart_dt.local.date()
        ).avg_value

        discharge_average_station2_expected = discharge_model_manual_second_hydro_station_kyrgyz.estimate_discharge(
            water_level_average_station2
        )

        virtual_average_discharge_expected = hydrological_round(
            virtual_station_association_one.weight / Decimal("100") * discharge_average_station1_expected
            + virtual_station_association_two.weight / Decimal("100") * discharge_average_station2_expected
        )

        virtual_discharge_average_estimated = EstimationsWaterDischargeDailyAverageVirtual.objects.get(
            station=virtual_station,
            timestamp_local__date=smart_dt.local.date(),
        ).avg_value

        assert custom_round(virtual_discharge_average_estimated, 6) == custom_round(
            virtual_average_discharge_expected, 6
        )
