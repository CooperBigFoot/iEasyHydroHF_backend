import pytest
from pytest_factoryboy import register

from .factories import StationFactory

register(StationFactory)


@pytest.fixture
def manual_station(db, station_factory):
    return station_factory.create(name="Manual station", is_automatic=False)


@pytest.fixture
def automatic_station(db, station_factory):
    return station_factory.create(name="Automatic station", is_automatic=True)
