import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from ninja_jwt.tokens import AccessToken
from pytest_factoryboy import register
from zoneinfo import ZoneInfo

from sapphire_backend.organizations.models import Organization
from sapphire_backend.organizations.tests.factories import BasinFactory, OrganizationFactory, RegionFactory
from sapphire_backend.stations.models import HydrologicalStation
from sapphire_backend.stations.tests.factories import (
    HydrologicalStationFactory,
    MeteorologicalStationFactory,
    SiteFactory,
)
from sapphire_backend.users.tests.factories import UserFactory

register(SiteFactory)
register(HydrologicalStationFactory)
register(UserFactory)
register(OrganizationFactory)
register(BasinFactory)
register(RegionFactory)

User = get_user_model()


@pytest.fixture
def organization(db, organization_factory=OrganizationFactory):
    return organization_factory.create(
        name="Kyrgyz Hydromet",
        language=Organization.Language.RUSSIAN,
        year_type=Organization.YearType.HYDROLOGICAL,
        timezone=ZoneInfo("Asia/Bishkek"),
    )


@pytest.fixture
def regular_user(db, organization):
    return UserFactory(username="regular_user", organization=organization)


@pytest.fixture
def backup_organization(db, organization_factory=OrganizationFactory):
    return organization_factory.create(
        name="Kazakh Hydromet",
        language=Organization.Language.RUSSIAN,
        year_type=Organization.YearType.HYDROLOGICAL,
        timezone=ZoneInfo("Asia/Almaty"),
    )


@pytest.fixture
def organization_admin(db, organization):
    return UserFactory(
        username="organization_admin", user_role=User.UserRoles.ORGANIZATION_ADMIN, organization=organization
    )


@pytest.fixture
def site_one(db, organization):
    return SiteFactory(country="Kyrgyzstan", organization=organization)


@pytest.fixture
def site_two(db, backup_organization):
    return SiteFactory(country="Kazakhstan", organization=backup_organization)


@pytest.fixture
def site_kyrgyz(db, backup_organization):
    return SiteFactory(country="Kyrgyzstan", organization=backup_organization, timezone=ZoneInfo("Asia/Bishkek"))


@pytest.fixture
def site_uzbek(db, backup_organization):
    return SiteFactory(country="Uzbekistan", organization=backup_organization, timezone=ZoneInfo("Asia/Tashkent"))


@pytest.fixture
def manual_hydro_station(db, site_one):
    return HydrologicalStationFactory(
        site=site_one,
        station_type=HydrologicalStation.StationType.MANUAL,
        station_code="12345",
        name="Manual Hydro Station",
    )


@pytest.fixture
def manual_hydro_station_kyrgyz(db, site_kyrgyz):
    return HydrologicalStationFactory(
        site=site_kyrgyz,
        station_type=HydrologicalStation.StationType.MANUAL,
        station_code="12345",
        name="Manual Kyrgyz Hydro Station",
    )


@pytest.fixture
def manual_hydro_station_uzbek(db, site_uzbek):
    return HydrologicalStationFactory(
        site=site_uzbek,
        station_type=HydrologicalStation.StationType.MANUAL,
        station_code="22345",
        name="Manual Uzbek Hydro Station",
    )


@pytest.fixture
def manual_meteo_station(db, site_one):
    return MeteorologicalStationFactory(site=site_one, station_code="12345", name="Manual Meteological Station")


@pytest.fixture
def manual_hydro_station_other_organization(db, site_two):
    return HydrologicalStationFactory(
        site=site_two,
        station_type=HydrologicalStation.StationType.MANUAL,
        station_code="56789",
        name="Manual Hydro Station Other Organization",
    )


@pytest.fixture
def automatic_hydro_station(db, site_one):
    return HydrologicalStationFactory(
        site=site_one,
        station_type=HydrologicalStation.StationType.AUTOMATIC,
        station_code="54321",
        name="Automatic Hydro Station",
    )


@pytest.fixture
def automatic_hydro_station_backup(db, site_one):
    return HydrologicalStationFactory(
        site=site_one,
        station_type=HydrologicalStation.StationType.AUTOMATIC,
        station_code="98765",
        name="Automatic Hydrological Station Backup",
    )


@pytest.fixture
def superadmin(db, organization):
    return UserFactory(username="superadmin", user_role=User.UserRoles.SUPER_ADMIN, organization=organization)


@pytest.fixture
def other_organization_user(db, backup_organization):
    return UserFactory(
        username="other_organization_user", user_role=User.UserRoles.REGULAR_USER, organization=backup_organization
    )


@pytest.fixture
def basin(db, organization):
    return BasinFactory(name="Basin One", organization=organization)


@pytest.fixture
def region(db, organization):
    return RegionFactory(name="Region One", organization=organization)


@pytest.fixture
def api_client():
    return Client()


@pytest.fixture
def authenticated_regular_user_api_client(regular_user):
    token = AccessToken.for_user(regular_user)
    client = Client(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def authenticated_organization_user_api_client(organization_admin):
    token = AccessToken.for_user(organization_admin)
    client = Client(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def authenticated_superadmin_user_api_client(superadmin):
    token = AccessToken.for_user(superadmin)
    client = Client(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def authenticated_regular_user_other_organization_api_client(other_organization_user):
    token = AccessToken.for_user(other_organization_user)
    client = Client(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client
