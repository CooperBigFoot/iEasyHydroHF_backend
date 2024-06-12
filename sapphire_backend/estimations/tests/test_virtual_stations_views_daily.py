import math
from datetime import timedelta
from decimal import Decimal

import pytest
from django.db import connection

from sapphire_backend.estimations.query import EstimationsViewQueryManager
from sapphire_backend.metrics.choices import HydrologicalMeasurementType, HydrologicalMetricName, MetricUnit
from sapphire_backend.metrics.models import HydrologicalMetric
from sapphire_backend.utils.datetime_helper import SmartDatetime


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

        discharge_morning_station1 = EstimationsViewQueryManager(
            model="estimations_water_discharge_daily",
            filter_dict={"station_id": manual_hydro_station_kyrgyz.id, "timestamp_local": smart_dt.morning_local},
        ).execute_query()[0]["avg_value"]

        discharge_morning_station2 = EstimationsViewQueryManager(
            model="estimations_water_discharge_daily",
            filter_dict={
                "station_id": manual_second_hydro_station_kyrgyz.id,
                "timestamp_local": smart_dt.morning_local,
            },
        ).execute_query()[0]["avg_value"]
        virtual_discharge_morning_expected = (
            virtual_station_association_one.weight / Decimal(100) * discharge_morning_station1
            + virtual_station_association_two.weight / Decimal(100) * discharge_morning_station2
        )

        virtual_discharge_morning_estimated = EstimationsViewQueryManager(
            model="estimations_water_discharge_daily_virtual",
            filter_dict={"station_id": virtual_station.id, "timestamp_local": smart_dt.morning_local},
        ).execute_query()[0]["avg_value"]

        assert round(float(virtual_discharge_morning_estimated), 6) == round(
            float(virtual_discharge_morning_expected), 6
        )

    def test_water_discharge_daily_morning_three_virtual_associations(
        self,
        organization,
        virtual_station,
        virtual_station_association_one,
        virtual_station_association_two,
        virtual_station_association_three,
        discharge_model_manual_hydro_station_kyrgyz,
        discharge_model_manual_second_hydro_station_kyrgyz,
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

        discharge_morning_station1 = EstimationsViewQueryManager(
            model="estimations_water_discharge_daily",
            filter_dict={"station_id": manual_hydro_station_kyrgyz.id, "timestamp_local": smart_dt.morning_local},
        ).execute_query()[0]["avg_value"]

        discharge_morning_station2 = EstimationsViewQueryManager(
            model="estimations_water_discharge_daily",
            filter_dict={
                "station_id": manual_second_hydro_station_kyrgyz.id,
                "timestamp_local": smart_dt.morning_local,
            },
        ).execute_query()[0]["avg_value"]
        discharge_morning_station3 = EstimationsViewQueryManager(
            model="estimations_water_discharge_daily",
            filter_dict={
                "station_id": manual_third_hydro_station_kyrgyz.id,
                "timestamp_local": smart_dt.morning_local,
            },
        ).execute_query()[0]["avg_value"]
        virtual_discharge_morning_expected = (
            virtual_station_association_one.weight / Decimal(100) * discharge_morning_station1
            + virtual_station_association_two.weight / Decimal(100) * discharge_morning_station2
            + virtual_station_association_three.weight / Decimal(100) * discharge_morning_station3
        )

        virtual_discharge_morning_estimated = EstimationsViewQueryManager(
            model="estimations_water_discharge_daily_virtual",
            filter_dict={"station_id": virtual_station.id, "timestamp_local": smart_dt.morning_local},
        ).execute_query()[0]["avg_value"]

        assert round(float(virtual_discharge_morning_estimated), 6) == round(
            float(virtual_discharge_morning_expected), 6
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

        discharge_evening_station1 = EstimationsViewQueryManager(
            model="estimations_water_discharge_daily",
            filter_dict={"station_id": manual_hydro_station_kyrgyz.id, "timestamp_local": smart_dt.evening_local},
        ).execute_query()[0]["avg_value"]

        discharge_evening_station2 = EstimationsViewQueryManager(
            model="estimations_water_discharge_daily",
            filter_dict={
                "station_id": manual_second_hydro_station_kyrgyz.id,
                "timestamp_local": smart_dt.evening_local,
            },
        ).execute_query()[0]["avg_value"]
        virtual_discharge_evening_expected = (
            virtual_station_association_one.weight / Decimal(100) * discharge_evening_station1
            + virtual_station_association_two.weight / Decimal(100) * discharge_evening_station2
        )

        virtual_discharge_evening_estimated = EstimationsViewQueryManager(
            model="estimations_water_discharge_daily_virtual",
            filter_dict={"station_id": virtual_station.id, "timestamp_local": smart_dt.evening_local},
        ).execute_query()[0]["avg_value"]

        assert round(float(virtual_discharge_evening_estimated), 6) == round(
            float(virtual_discharge_evening_expected), 6
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
        water_level_average_station1 = math.ceil(
            (water_level_morning_station1.avg_value + water_level_evening_station1.avg_value) / 2
        )
        discharge_average_station1_expected = discharge_model_manual_hydro_station_kyrgyz.estimate_discharge(
            water_level_average_station1
        )

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

        water_level_average_station2 = math.ceil(
            (water_level_morning_station2.avg_value + water_level_evening_station2.avg_value) / 2
        )
        discharge_average_station2_expected = discharge_model_manual_second_hydro_station_kyrgyz.estimate_discharge(
            water_level_average_station2
        )

        virtual_average_discharge_expected = (
            virtual_station_association_one.weight / 100 * discharge_average_station1_expected
            + virtual_station_association_two.weight / 100 * discharge_average_station2_expected
        )

        with connection.cursor() as cursor:
            cursor.execute(
                "CALL refresh_continuous_aggregate('test_sapphire_backend.public.estimations_water_level_daily_average', '2015-01-01', '2025-04-10')"
            )

        virtual_discharge_average_estimated = EstimationsViewQueryManager(
            model="estimations_water_discharge_daily_average_virtual",
            filter_dict={"station_id": virtual_station.id, "timestamp_local": smart_dt.midday_local},
        ).execute_query()[0]["avg_value"]

        assert round(float(virtual_discharge_average_estimated), 6) == round(
            float(virtual_average_discharge_expected), 6
        )
