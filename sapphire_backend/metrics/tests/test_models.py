import pytest
from django.db import connection


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
