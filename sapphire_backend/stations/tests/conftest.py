import pytest
from pytest_factoryboy import register

from .factories import (
    HydrologicalStation,
    HydrologicalStationFactory,
    SiteFactory,
    VirtualStationAssociationFactory,
    VirtualStationFactory,
)

register(SiteFactory)
register(HydrologicalStationFactory)
register(VirtualStationFactory)
register(VirtualStationAssociationFactory)


@pytest.fixture
def another_site_station(db, hydro_station_factory, site_two):
    return hydro_station_factory.create(site=site_two, station_type=HydrologicalStation.StationType.AUTOMATIC)


@pytest.fixture
def virtual_station(db, organization):
    return VirtualStationFactory(name="Virtual Station Main", organization=organization, station_code="11111")


@pytest.fixture
def virtual_station_no_associations(db, organization):
    return VirtualStationFactory(
        name="Virtual Station No Associations", organization=organization, station_code="22222"
    )


@pytest.fixture
def virtual_station_backup_organization(db, backup_organization):
    return VirtualStationFactory(
        name="Virtual Station Other Organization", organization=backup_organization, station_code="33333"
    )


@pytest.fixture
def virtual_station_deleted(db, organization):
    return VirtualStationFactory(
        name="Deleted Virtual Station", organization=organization, is_deleted=True, station_code="44444"
    )


@pytest.fixture
def virtual_station_association_one(db, automatic_hydro_station, virtual_station):
    return VirtualStationAssociationFactory(
        virtual_station=virtual_station, hydro_station=automatic_hydro_station, weight=0.5
    )


@pytest.fixture
def virtual_station_association_two(db, manual_hydro_station, virtual_station):
    return VirtualStationAssociationFactory(
        virtual_station=virtual_station, hydro_station=manual_hydro_station, weight=0.5
    )
