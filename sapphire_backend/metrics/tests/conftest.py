import pytest
from pytest_factoryboy import register

from .factories import HydrologicalMetricFactory, MeteorologicalMetricFactory

register(HydrologicalMetricFactory)
register(MeteorologicalMetricFactory)


@pytest.fixture
def water_level_metric(db, hydrological_metric_factory=HydrologicalMetricFactory):
    return hydrological_metric_factory.create()
