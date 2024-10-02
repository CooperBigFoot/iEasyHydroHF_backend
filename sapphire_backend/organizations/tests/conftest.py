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
def chu_basin(db, organization_kyrgyz):
    return BasinFactory(name="Чу", organization=organization_kyrgyz)


@pytest.fixture
def talas_basin(db, organization_kyrgyz):
    return BasinFactory(name="Талас", organization=organization_kyrgyz)


@pytest.fixture
def talas_region(db, organization_kyrgyz):
    return RegionFactory(name="ТАЛАССКАЯ ОБЛАСТЬ", organization=organization_kyrgyz)


@pytest.fixture
def osh_region(db, organization_kyrgyz):
    return RegionFactory(name="Ошская область", organization=organization_kyrgyz)
