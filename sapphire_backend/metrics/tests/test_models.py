import pytest
from django.db import connection


class TestMetricsModelController:
    @pytest.mark.django_db
    def test_hypertable_count(self):
        with connection.cursor() as c:
            c.execute("SELECT COUNT(*) FROM timescaledb_information.hypertables;")
            r = c.fetchone()
            assert r[0] == 5

    @pytest.mark.django_db
    def test_hypertable_names(self):
        with connection.cursor() as c:
            c.execute("SELECT * FROM timescaledb_information.hypertables;")
            r = c.fetchall()

            EXPECTED_HYPERTABLES = [
                "metrics_air_temperature",
                "metrics_water_temperature",
                "metrics_water_discharge",
                "metrics_water_level",
                "metrics_water_velocity",
            ]

            ACTUAL_HYPERTABLES = [record[1] for record in r]

            assert EXPECTED_HYPERTABLES.sort() == ACTUAL_HYPERTABLES.sort()
