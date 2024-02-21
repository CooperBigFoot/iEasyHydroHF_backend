import pytest
from pytest_factoryboy import register

from .factories import HydrologicalStation, HydrologicalStationFactory, SiteFactory

register(SiteFactory)
register(HydrologicalStationFactory)


@pytest.fixture
def another_site_station(db, hydro_station_factory, site_two):
    return hydro_station_factory.create(site=site_two, station_type=HydrologicalStation.StationType.AUTOMATIC)
