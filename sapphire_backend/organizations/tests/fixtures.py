import pytest
import pytz
from pytest_factoryboy import register

from ..models import Organization
from .factories import OrganizationFactory

register(OrganizationFactory)


@pytest.fixture
def organization(db, organization_factory):
    return organization_factory.create(
        name="Kyrgyz Hydromet",
        language=Organization.Language.RUSSIAN,
        year_type=Organization.YearType.HYDROLOGICAL,
        timezone=pytz.timezone("Asia/Bishkek"),
    )
