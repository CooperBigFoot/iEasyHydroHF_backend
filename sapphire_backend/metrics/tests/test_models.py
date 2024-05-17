import datetime
from zoneinfo import ZoneInfo

import pytest
from django.db import connection

from sapphire_backend.metrics.choices import (
    HydrologicalMeasurementType,
    HydrologicalMetricName,
    MeteorologicalMetricName,
    MetricUnit, MeteorologicalMeasurementType,
)
from sapphire_backend.metrics.models import HydrologicalMetric, MeteorologicalMetric


class TestMetricsModel:
    @pytest.mark.django_db
    def test_hypertable_count(self):
        with connection.cursor() as c:
            c.execute("SELECT COUNT(*) FROM timescaledb_information.hypertables;")
            r = c.fetchone()
            assert r[0] == 2

    @pytest.mark.django_db
    def test_hypertable_names(self):
        with connection.cursor() as c:
            c.execute("SELECT * FROM timescaledb_information.hypertables;")
            r = c.fetchall()

            EXPECTED_HYPERTABLES = ["metrics_hydrologicalmetric", "metrics_meteorologicalmetric"]

            ACTUAL_HYPERTABLES = [record[1] for record in r]

            assert sorted(EXPECTED_HYPERTABLES) == sorted(ACTUAL_HYPERTABLES)

    @pytest.mark.django_db(transaction=True)
    def test_hydro_metric_save(self, manual_hydro_station):
        hydro_metric = HydrologicalMetric(
            timestamp=datetime.datetime.utcnow(),
            avg_value=15.5,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_hydro_station,
        )

        hydro_metric.save()

        assert HydrologicalMetric.objects.count() == 1
        assert HydrologicalMetric.objects.last().avg_value == 15.5

    @pytest.mark.django_db(transaction=True)
    def test_hydro_metric_save_with_upsert(self, manual_hydro_station):
        now_dt = datetime.datetime.utcnow()

        hydro_metric = HydrologicalMetric(
            timestamp=now_dt,
            avg_value=15.5,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_hydro_station,
        )
        hydro_metric.save()

        hydro_metric_for_update = HydrologicalMetric(
            timestamp=now_dt,
            avg_value=20.0,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_hydro_station,
        )

        hydro_metric_for_update.save(upsert=True)

        assert HydrologicalMetric.objects.count() == 1
        assert HydrologicalMetric.objects.last().avg_value == 20.0

    @pytest.mark.django_db(transaction=True)
    def test_hydro_metric_delete(self, manual_hydro_station):
        hydro_metric = HydrologicalMetric(
            timestamp=datetime.datetime.utcnow(),
            avg_value=15.5,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_hydro_station,
        )

        hydro_metric.save()

        metric_from_db = HydrologicalMetric.objects.last()

        metric_from_db.delete()

        assert HydrologicalMetric.objects.exists() is False

    def test_meteo_metric_save(self, manual_meteo_station):
        meteo_metric = MeteorologicalMetric(
            timestamp=datetime.datetime.utcnow(),
            value=15.5,
            unit=MetricUnit.TEMPERATURE,
            metric_name=MeteorologicalMetricName.AIR_TEMPERATURE_DECADE_AVERAGE,
            station=manual_meteo_station,
        )

        meteo_metric.save()

        assert MeteorologicalMetric.objects.count() == 1
        assert MeteorologicalMetric.objects.last().value == 15.5

    def test_meteo_metric_save_with_upsert(self, manual_meteo_station):
        now_dt = datetime.datetime.utcnow()

        meteo_metric = MeteorologicalMetric(
            timestamp=now_dt,
            value=15.5,
            unit=MetricUnit.TEMPERATURE,
            metric_name=MeteorologicalMetricName.AIR_TEMPERATURE_DECADE_AVERAGE,
            station=manual_meteo_station,
        )

        meteo_metric.save()

        meteo_metric_for_update = MeteorologicalMetric(
            timestamp=now_dt,
            value=20,
            unit=MetricUnit.TEMPERATURE,
            metric_name=MeteorologicalMetricName.AIR_TEMPERATURE_DECADE_AVERAGE,
            station=manual_meteo_station,
        )

        meteo_metric_for_update.save(upsert=True)

        assert MeteorologicalMetric.objects.count() == 1
        assert MeteorologicalMetric.objects.last().value == 20.0

    def test_meteo_metric_delete(self, manual_meteo_station):
        meteo_metric = MeteorologicalMetric(
            timestamp=datetime.datetime.utcnow(),
            value=15.5,
            unit=MetricUnit.TEMPERATURE,
            metric_name=MeteorologicalMetricName.AIR_TEMPERATURE_DECADE_AVERAGE,
            station=manual_meteo_station,
        )

        meteo_metric.save()

        metric_from_db = MeteorologicalMetric.objects.last()

        metric_from_db.delete()

        assert MeteorologicalMetric.objects.exists() is False

    def test_hydro_metric_instantiate_with_timestamp_local(self, manual_hydro_station_kyrgyz):
        timestamp_morning_tz = datetime.datetime(2020, 1, 1, 8, 0, 0, tzinfo=manual_hydro_station_kyrgyz.timezone)
        timestamp_morning_local = datetime.datetime(2020, 1, 1, 8, 0, 0, tzinfo=ZoneInfo('UTC'))

        hydro_metric = HydrologicalMetric(
            timestamp_local=timestamp_morning_local,
            avg_value=12.7,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_hydro_station_kyrgyz,
        )

        assert hydro_metric.timestamp == timestamp_morning_tz
        assert hydro_metric.timestamp_local == timestamp_morning_local

    def test_hydro_metric_instantiate_with_timestamp(self, manual_hydro_station_kyrgyz):
        timestamp_morning_tz = datetime.datetime(2020, 1, 1, 8, 0, 0, tzinfo=manual_hydro_station_kyrgyz.timezone)
        timestamp_morning_local = datetime.datetime(2020, 1, 1, 8, 0, 0, tzinfo=ZoneInfo('UTC'))

        hydro_metric = HydrologicalMetric(
            timestamp=timestamp_morning_tz,
            avg_value=12.7,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_hydro_station_kyrgyz,
        )

        assert hydro_metric.timestamp == timestamp_morning_tz
        assert hydro_metric.timestamp_local == timestamp_morning_local

    def test_meteo_metric_instantiate_with_timestamp_local(self, manual_meteo_station_kyrgyz):
        timestamp_morning_tz = datetime.datetime(2020, 1, 1, 8, 0, 0, tzinfo=manual_meteo_station_kyrgyz.timezone)
        timestamp_morning_local = datetime.datetime(2020, 1, 1, 8, 0, 0, tzinfo=ZoneInfo('UTC'))

        meteo_metric = MeteorologicalMetric(
            timestamp_local=timestamp_morning_local,
            value=10.7,
            unit=MetricUnit.TEMPERATURE,
            metric_name=MeteorologicalMetricName.AIR_TEMPERATURE_DECADE_AVERAGE,
            value_type=MeteorologicalMeasurementType.MANUAL,
            station=manual_meteo_station_kyrgyz,
        )

        assert meteo_metric.timestamp == timestamp_morning_tz
        assert meteo_metric.timestamp_local == timestamp_morning_local

    def test_meteo_metric_instantiate_with_timestamp(self, manual_meteo_station_kyrgyz):
        timestamp_morning_tz = datetime.datetime(2020, 1, 1, 8, 0, 0, tzinfo=manual_meteo_station_kyrgyz.timezone)
        timestamp_morning_local = datetime.datetime(2020, 1, 1, 8, 0, 0, tzinfo=ZoneInfo('UTC'))

        meteo_metric = MeteorologicalMetric(
            timestamp=timestamp_morning_tz,
            value=9.7,
            unit=MetricUnit.TEMPERATURE,
            metric_name=MeteorologicalMetricName.AIR_TEMPERATURE_DECADE_AVERAGE,
            value_type=MeteorologicalMeasurementType.MANUAL,
            station=manual_meteo_station_kyrgyz,
        )

        assert meteo_metric.timestamp == timestamp_morning_tz
        assert meteo_metric.timestamp_local == timestamp_morning_local
