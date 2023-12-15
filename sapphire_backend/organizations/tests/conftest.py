import pytest
from pytest_factoryboy import register
from zoneinfo import ZoneInfo

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
def basin(db, basin_factory, organization):
    return basin_factory.create(name="Basin One", organization=organization)


@pytest.fixture
def region(db, region_factory, organization):
    return region_factory.create(name="Region One", organization=organization)
