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
