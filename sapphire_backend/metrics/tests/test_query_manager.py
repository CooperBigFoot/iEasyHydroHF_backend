import datetime

import pytest

from sapphire_backend.metrics.choices import HydrologicalMetricName
from sapphire_backend.metrics.models import HydrologicalMetric
from sapphire_backend.metrics.timeseries.query import TimeseriesQueryManager


class TestTimeseriesQueryManager:
    def test_invalid_model(self):
        with pytest.raises(ValueError) as e:
            _ = TimeseriesQueryManager(None, "123")

            assert (
                str(e)
                == "TimeseriesQueryManager can only be instantiated with HydrologicalMetric or MeteorologicalMetric."
            )

    @pytest.mark.django_db
    def test_invalid_organization_uuid(self):
        with pytest.raises(ValueError) as e:
            _ = TimeseriesQueryManager(HydrologicalMetric, "aaaa1111-bb22-cc33-dd44-eee555fff666")

            assert str(e) == "Organization with the given UUID does not exist."

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
        dt_now = datetime.datetime.utcnow()
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
        with pytest.raises(ValueError) as e:
            _ = TimeseriesQueryManager(HydrologicalMetric, organization.uuid, filter_dict={"some_field": "some_value"})

            assert str(e) == "some_field field does not exist on HydrologicalMetric"
