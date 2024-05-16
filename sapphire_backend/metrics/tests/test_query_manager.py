import datetime as dt

import pytest

from sapphire_backend.metrics.choices import HydrologicalMeasurementType, HydrologicalMetricName
from sapphire_backend.metrics.models import HydrologicalMetric, MeteorologicalMetric
from sapphire_backend.metrics.timeseries.query import TimeseriesQueryManager


class TestTimeseriesQueryManager:
    def test_invalid_model(self):
        with pytest.raises(
            ValueError,
            match="TimeseriesQueryManager can only be instantiated with HydrologicalMetric or MeteorologicalMetric.",
        ):
            _ = TimeseriesQueryManager(None, "123")

    @pytest.mark.django_db
    def test_invalid_organization_uuid(self):
        with pytest.raises(ValueError, match="Organization with the given UUID does not exist."):
            _ = TimeseriesQueryManager(HydrologicalMetric, "aaaa1111-bb22-cc33-dd44-eee555fff666")

    def test_order_resolve(self, organization):
        descending_timestamp_query_manager = TimeseriesQueryManager(
            HydrologicalMetric, organization.uuid, order_param="timestamp", order_direction="DESC"
        )
        ascending_average_value_query_manager = TimeseriesQueryManager(
            HydrologicalMetric, organization.uuid, order_param="avg_value", order_direction="ASC"
        )

        assert descending_timestamp_query_manager.order == "-timestamp"
        assert ascending_average_value_query_manager.order == "avg_value"

    def test_orm_filter_construction_for_no_explicit_filter(self, organization):
        query_manager = TimeseriesQueryManager(HydrologicalMetric, organization.uuid)

        assert query_manager.filter == {"station__site__organization": organization.uuid}

    def test_orm_filter_construction_for_filter_dict(self, organization):
        dt_now = dt.datetime.utcnow()
        query_manager = TimeseriesQueryManager(
            HydrologicalMetric,
            organization.uuid,
            filter_dict={
                "timestamp__lte": dt_now.isoformat(),
                "metric_name": HydrologicalMetricName.WATER_LEVEL_DAILY,
            },
        )

        assert query_manager.filter == {
            "station__site__organization": organization.uuid,
            "timestamp__lte": dt_now.isoformat(),
            "metric_name": HydrologicalMetricName.WATER_LEVEL_DAILY,
        }

    def test_orm_filter_construction_for_invalid_field(self, organization):
        with pytest.raises(ValueError, match="some_field field does not exist on the HydrologicalMetric model."):
            _ = TimeseriesQueryManager(HydrologicalMetric, organization.uuid, filter_dict={"some_field": "some_value"})

    def test_raw_sql_organization_join(self, organization):
        query_manager = TimeseriesQueryManager(MeteorologicalMetric, organization_uuid=organization.uuid)

        assert (
            query_manager._construct_organization_sql_join_string()
            == """
            JOIN stations_meteorologicalstation st ON st.id = metrics_meteorologicalmetric.station_id
            JOIN stations_site s ON s.uuid = st.site_id
            JOIN organizations_organization o ON o.uuid = s.organization_id
        """
        )

    def test_raw_sql_filter_construction_for_no_explicit_filter(self, organization):
        query_manager = TimeseriesQueryManager(HydrologicalMetric, organization_uuid=organization.uuid)

        assert query_manager._construct_sql_filter_string() == (f"o.uuid='{organization.uuid}'", [])

    def test_raw_sql_filter_construction_for_simple_filter(self, organization, manual_hydro_station):
        query_manager = TimeseriesQueryManager(
            HydrologicalMetric,
            organization_uuid=organization.uuid,
            filter_dict={
                "timestamp__gte": "2020-01-01T00:00:00Z",
                "station": manual_hydro_station.id,
            },
        )

        assert query_manager._construct_sql_filter_string() == (
            f"o.uuid='{organization.uuid}' AND timestamp >= %s AND st.id = %s",
            ["2020-01-01T00:00:00Z", manual_hydro_station.id],
        )

    def test_raw_sql_filter_construction_for_array_filter(self, organization):
        query_manager = TimeseriesQueryManager(
            HydrologicalMetric,
            organization_uuid=organization.uuid,
            filter_dict={
                "timestamp__gte": "2020-01-01T00:00:00Z",
                "metric_name__in": [
                    HydrologicalMetricName.WATER_LEVEL_DAILY,
                    HydrologicalMetricName.WATER_DISCHARGE_DAILY,
                ],
                "station__station_code__in": ["1", "2", "3"],
                "value_type__in": [HydrologicalMeasurementType.MANUAL],
            },
        )

        assert query_manager._construct_sql_filter_string() == (
            f"o.uuid='{organization.uuid}' AND timestamp >= %s AND metric_name IN (%s, %s) "
            f"AND st.station_code IN (%s, %s, %s) AND value_type IN (%s)",
            ["2020-01-01T00:00:00Z", "WLD", "WDD", "1", "2", "3", "M"],
        )

    def test_raw_sql_filter_construction_for_invalid_field(self, organization):
        with pytest.raises(
            ValueError, match="non_existing_field field does not exist on the HydrologicalMetric model."
        ):
            _ = TimeseriesQueryManager(
                HydrologicalMetric,
                organization_uuid=organization.uuid,
                filter_dict={
                    "non_existing_field": "some_value",
                },
            )

    def test_execute_query_for_no_filters(
        self,
        organization,
        water_level_manual,
        water_level_automatic,
        water_level_manual_other,
        water_level_manual_other_organization,
        water_discharge,
    ):
        query_manager = TimeseriesQueryManager(HydrologicalMetric, organization_uuid=organization.uuid)
        results = query_manager.execute_query()

        assert results.count() == 4
        assert list(results) == [water_discharge, water_level_manual_other, water_level_automatic, water_level_manual]

    def test_query_manager_with_timestamp_filter(
        self,
        organization,
        water_level_manual,
        water_level_manual_other,
        water_level_manual_other_organization,
        water_discharge,
    ):
        query_dt = dt.datetime.now(tz=dt.timezone.utc) - dt.timedelta(hours=36)

        query_manager = TimeseriesQueryManager(
            HydrologicalMetric,
            organization_uuid=organization.uuid,
            filter_dict={
                "timestamp__gte": query_dt.isoformat(),
            },
        )

        results = query_manager.execute_query()
        assert results.count() == 2
        assert list(results) == [water_discharge, water_level_manual_other]

    def test_query_manager_with_metric_type_filter(
        self, organization, water_level_manual, water_level_automatic, water_level_manual_other, water_discharge
    ):
        query_manager = TimeseriesQueryManager(
            HydrologicalMetric,
            organization_uuid=organization.uuid,
            filter_dict={"value_type": HydrologicalMeasurementType.MANUAL},
        )

        assert query_manager.execute_query().count() == 2

    def test_query_manager_with_station_list_filter(
        self,
        organization,
        water_level_manual,
        water_level_manual_other,
        water_level_automatic,
        water_discharge,
        manual_hydro_station,
    ):
        query_manager = TimeseriesQueryManager(
            HydrologicalMetric,
            organization_uuid=organization.uuid,
            filter_dict={"station__station_code__in": [manual_hydro_station.station_code]},
        )

        assert query_manager.execute_query().count() == 3

    def test_query_manager_with_metric_name_filter(
        self,
        organization,
        water_level_manual,
        water_level_automatic,
        water_level_manual_other,
        water_discharge,
        water_level_manual_other_organization,
    ):
        query_manager = TimeseriesQueryManager(
            HydrologicalMetric,
            organization_uuid=organization.uuid,
            filter_dict={"metric_name": HydrologicalMetricName.WATER_LEVEL_DAILY},
        )

        assert query_manager.execute_query().count() == 3

    def test_query_manager_change_order(
        self,
        organization,
        water_level_manual,
        water_level_automatic,
        water_level_manual_other,
        water_discharge,
        water_level_manual_other_organization,
    ):
        query_manager = TimeseriesQueryManager(
            HydrologicalMetric, organization_uuid=organization.uuid, order_direction="ASC"
        )

        results = query_manager.execute_query()
        assert results.count() == 4
        assert list(results) == [water_level_manual, water_level_automatic, water_level_manual_other, water_discharge]

    def test_query_manager_get_total(
        self,
        organization,
        water_level_manual,
        water_level_automatic,
        water_level_manual_other,
        water_discharge,
        water_level_manual_other_organization,
    ):
        query_manager = TimeseriesQueryManager(HydrologicalMetric, organization_uuid=organization.uuid)

        assert query_manager.get_total() == 4

    def test_query_manager_get_metric_distribution(
        self,
        organization,
        water_level_manual,
        water_level_automatic,
        water_discharge,
        water_level_manual_other,
        water_level_manual_other_organization,
    ):
        query_manager = TimeseriesQueryManager(HydrologicalMetric, organization_uuid=organization.uuid)

        results = query_manager.get_metric_distribution()
        assert len(results) == 2

        EXPECTED_OUTPUTS = [
            {"metric_name": HydrologicalMetricName.WATER_LEVEL_DAILY, "metric_count": 3},
            {"metric_name": HydrologicalMetricName.WATER_DISCHARGE_DAILY, "metric_count": 1},
        ]

        for output in EXPECTED_OUTPUTS:
            assert output in list(results)

    def test_query_manager_time_bucket_for_invalid_interval(
        self, organization, water_level_manual, water_level_manual_other, water_level_automatic, water_discharge
    ):
        query_manager = TimeseriesQueryManager(HydrologicalMetric, organization_uuid=organization.uuid)

        with pytest.raises(ValueError, match="Invalid time bucket interval"):
            _ = query_manager.time_bucket("error", "avg")

    def test_query_manager_time_bucket_for_invalid_function(
        self, organization, water_level_manual, water_level_manual_other, water_level_automatic, water_discharge
    ):
        query_manager = TimeseriesQueryManager(HydrologicalMetric, organization_uuid=organization.uuid)

        with pytest.raises(ValueError, match="Invalid aggregation function"):
            _ = query_manager.time_bucket("1 day", "error")

    def test_query_manager_time_bucket_for_daily_count_interval(
        self, organization, water_level_manual, water_level_manual_other, water_level_automatic, water_discharge
    ):
        query_manager = TimeseriesQueryManager(HydrologicalMetric, organization_uuid=organization.uuid)

        results = query_manager.time_bucket("1 day", "count")

        assert results == [
            {
                "bucket": dt.datetime(
                    water_discharge.timestamp.year,
                    water_discharge.timestamp.month,
                    water_discharge.timestamp.day,
                    tzinfo=dt.timezone.utc,
                ),
                "value": 1,
            },
            {
                "bucket": dt.datetime(
                    water_level_manual_other.timestamp.year,
                    water_level_manual_other.timestamp.month,
                    water_level_manual_other.timestamp.day,
                    tzinfo=dt.timezone.utc,
                ),
                "value": 1,
            },
            {
                "bucket": dt.datetime(
                    water_level_automatic.timestamp.year,
                    water_level_automatic.timestamp.month,
                    water_level_automatic.timestamp.day,
                    tzinfo=dt.timezone.utc,
                ),
                "value": 1,
            },
            {
                "bucket": dt.datetime(
                    water_level_manual.timestamp.year,
                    water_level_manual.timestamp.month,
                    water_level_manual.timestamp.day,
                    tzinfo=dt.timezone.utc,
                ),
                "value": 1,
            },
        ]

    def test_query_manager_time_bucket_for_daily_average_interval_with_timestamp_filter(
        self, organization, water_level_manual, water_level_manual_other, water_level_automatic, water_discharge
    ):
        query_manager = TimeseriesQueryManager(
            HydrologicalMetric,
            organization_uuid=organization.uuid,
            filter_dict={"timestamp__gte": (dt.datetime.utcnow() - dt.timedelta(hours=36)).isoformat()},
        )

        results = query_manager.time_bucket("1 day", "avg")

        assert results == [
            {
                "bucket": dt.datetime(
                    water_discharge.timestamp.year,
                    water_discharge.timestamp.month,
                    water_discharge.timestamp.day,
                    tzinfo=dt.timezone.utc,
                ),
                "value": 2.0,
            },
            {
                "bucket": dt.datetime(
                    water_level_manual_other.timestamp.year,
                    water_level_manual_other.timestamp.month,
                    water_level_manual_other.timestamp.day,
                    tzinfo=dt.timezone.utc,
                ),
                "value": 10.0,
            },
        ]

    def test_query_manager_time_bucket_for_daily_average_interval_with_station_filter(
        self,
        organization,
        water_level_manual,
        water_level_manual_other,
        water_level_automatic,
        water_discharge,
        automatic_hydro_station,
    ):
        query_manager = TimeseriesQueryManager(
            HydrologicalMetric,
            organization_uuid=organization.uuid,
            filter_dict={"station__station_code__in": [automatic_hydro_station.station_code]},
        )

        results = query_manager.time_bucket("1 day", "count")

        assert results == [
            {
                "bucket": dt.datetime(
                    water_level_automatic.timestamp.year,
                    water_level_automatic.timestamp.month,
                    water_level_automatic.timestamp.day,
                    tzinfo=dt.timezone.utc,
                ),
                "value": 1,
            }
        ]
