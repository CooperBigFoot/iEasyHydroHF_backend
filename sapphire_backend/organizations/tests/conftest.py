import pytest
from pytest_factoryboy import register
from zoneinfo import ZoneInfo

from sapphire_backend.stations.tests.factories import SiteFactory, VirtualStationFactory

from ..models import Organization
from .factories import BasinFactory, OrganizationFactory, RegionFactory

register(BasinFactory)
register(OrganizationFactory)
register(RegionFactory)


@pytest.fixture
def other_organization(db, organization_factory):
    return organization_factory.create(
        name="Kazakh Hydromet",
        language=Organization.Language.RUSSIAN,
        year_type=Organization.YearType.HYDROLOGICAL,
        timezone=ZoneInfo("Asia/Almaty"),
    )


@pytest.fixture
def kyrgyz_hydromet(db):
    return OrganizationFactory(
        name="КыргызГидроМет", language=Organization.Language.RUSSIAN, timezone=ZoneInfo("Asia/Bishkek")
    )


@pytest.fixture
def chu_basin(db, kyrgyz_hydromet):
    return BasinFactory(name="Чу", organization=kyrgyz_hydromet)


@pytest.fixture
def dummy_basin(db, kyrgyz_hydromet):
    return BasinFactory(name="Dummy", organization=kyrgyz_hydromet)


@pytest.fixture
def dummy_region(db, kyrgyz_hydromet):
    return RegionFactory(name="Dummy", organization=kyrgyz_hydromet)


@pytest.fixture
def talas_basin(db, kyrgyz_hydromet):
    return BasinFactory(name="Талас", organization=kyrgyz_hydromet)


@pytest.fixture
def talas_region(db, kyrgyz_hydromet):
    return RegionFactory(name="ТАЛАССКАЯ ОБЛАСТЬ", organization=kyrgyz_hydromet)


@pytest.fixture
def osh_region(db, kyrgyz_hydromet):
    return RegionFactory(name="Ошская область", organization=kyrgyz_hydromet)


@pytest.fixture
def chu_site(db, kyrgyz_hydromet, chu_basin):
    return SiteFactory(country="Kyrgyzstan", organization=kyrgyz_hydromet, basin=chu_basin)


@pytest.fixture
def talas_site(db, kyrgyz_hydromet, talas_basin, talas_region):
    return SiteFactory(country="Kyrgyzstan", organization=kyrgyz_hydromet, basin=talas_basin, region=talas_region)


@pytest.fixture
def osh_site(db, kyrgyz_hydromet, osh_region):
    return SiteFactory(country="Kyrgyzstan", organization=kyrgyz_hydromet, region=osh_region)


@pytest.fixture
def dummy_site(db, kyrgyz_hydromet, dummy_basin, dummy_region):
    return SiteFactory(country="Kyrgyzstan", organization=kyrgyz_hydromet, basin=dummy_basin, region=dummy_region)


@pytest.fixture
def chu_virtual_station(db, kyrgyz_hydromet, chu_basin):
    return VirtualStationFactory(
        name="Virtual Station Chu", organization=kyrgyz_hydromet, station_code="77777", basin=chu_basin
    )


@pytest.fixture
def talas_virtual_station(db, kyrgyz_hydromet, talas_basin, talas_region):
    return VirtualStationFactory(
        name="Virtual Station Talas",
        organization=kyrgyz_hydromet,
        station_code="88888",
        basin=talas_basin,
        region=talas_region,
    )


@pytest.fixture
def osh_virtual_station(db, kyrgyz_hydromet, osh_region):
    return VirtualStationFactory(
        name="Virtual Station Osh", organization=kyrgyz_hydromet, station_code="99999", region=osh_region
    )
