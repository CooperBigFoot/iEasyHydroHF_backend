import pytest
from pytest_factoryboy import register

from .factories import HydrologicalStation, HydrologicalStationFactory, SiteFactory

register(SiteFactory)
register(HydrologicalStationFactory)


@pytest.fixture
def site_one(db, site_factory):
    return site_factory.create("Site one")


@pytest.fixture
def site_two(db, site_factory):
    return site_factory.create("Site two")


@pytest.fixture
def manual_hydro_station(db, hydro_station_factory):
    return hydro_station_factory.create(
        name="Manual hydro station", site=site_one, station_type=HydrologicalStation.StationType.MANUAL
    )


@pytest.fixture
def automatic_hydro_station(db, hydro_station_factory):
    return hydro_station_factory.create(
        name="Manual hydro station", site=site_one, station_type=HydrologicalStation.StationType.AUTOMATIC
    )
