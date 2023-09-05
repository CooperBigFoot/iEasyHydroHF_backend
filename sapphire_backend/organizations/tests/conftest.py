from zoneinfo import ZoneInfo

import pytest
from pytest_factoryboy import register

from ..models import Organization
from .factories import OrganizationFactory

register(OrganizationFactory)


@pytest.fixture
def other_organization(db, organization_factory):
    return organization_factory.create(
        name="Kazakh Hydromet",
        language=Organization.Language.RUSSIAN,
        year_type=Organization.YearType.HYDROLOGICAL,
        timezone=ZoneInfo("Asia/Almaty"),
    )
