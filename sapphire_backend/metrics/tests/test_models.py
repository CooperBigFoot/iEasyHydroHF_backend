import datetime

import pytest
from django.db import connection

from sapphire_backend.metrics.choices import (
    HydrologicalMeasurementType,
    HydrologicalMetricName,
    MetricUnit,
)
from sapphire_backend.metrics.models import HydrologicalMetric


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

    def test_save(self, manual_hydro_station):
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

    def test_save_with_upsert(self, manual_hydro_station):
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

    def test_delete(self, manual_hydro_station):
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
