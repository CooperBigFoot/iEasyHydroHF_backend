import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from pytest_factoryboy import register
from zoneinfo import ZoneInfo

from sapphire_backend.ingestion.tests.factories import FileStateFactory
from sapphire_backend.organizations.models import Organization
from sapphire_backend.organizations.tests.factories import BasinFactory, OrganizationFactory, RegionFactory
from sapphire_backend.stations.models import HydrologicalStation
from sapphire_backend.stations.tests.factories import (
    HydrologicalStationFactory,
    MeteorologicalStationFactory,
    SiteFactory,
)
from sapphire_backend.users.conftest import get_api_client_for_user
from sapphire_backend.users.tests.factories import UserFactory

register(SiteFactory)
register(HydrologicalStationFactory)
register(UserFactory)
register(OrganizationFactory)
register(BasinFactory)
register(RegionFactory)
register(FileStateFactory)
User = get_user_model()


# organizations
@pytest.fixture
def organization(db, organization_factory=OrganizationFactory):
    return organization_factory.create(
        name="Kyrgyz Hydromet",
        language=Organization.Language.RUSSIAN,
        year_type=Organization.YearType.HYDROLOGICAL,
        timezone=ZoneInfo("Asia/Bishkek"),
    )


@pytest.fixture
def organization_kyrgyz(db, organization_factory=OrganizationFactory):
    return organization_factory.create(
        name="Kyrgyz Hydromet",
        language=Organization.Language.RUSSIAN,
        year_type=Organization.YearType.HYDROLOGICAL,
        timezone=ZoneInfo("Asia/Bishkek"),
    )


@pytest.fixture
def organization_uzbek(db, organization_factory=OrganizationFactory):
    return organization_factory.create(
        name="Uzbek Gidromet",
        language=Organization.Language.RUSSIAN,
        year_type=Organization.YearType.HYDROLOGICAL,
        timezone=ZoneInfo("Asia/Tashkent"),
    )


@pytest.fixture
def backup_organization(db, organization_factory=OrganizationFactory):
    return organization_factory.create(
        name="Kazakh Hydromet",
        language=Organization.Language.RUSSIAN,
        year_type=Organization.YearType.HYDROLOGICAL,
        timezone=ZoneInfo("Asia/Almaty"),
    )


# basins
@pytest.fixture
def basin(db, organization):
    return BasinFactory(name="Basin One", organization=organization)


# regions
@pytest.fixture
def region(db, organization):
    return RegionFactory(name="Region One", organization=organization)


# users
@pytest.fixture
def regular_user(db, organization):
    return UserFactory(username="regular_user", organization=organization)


@pytest.fixture
def regular_user_kyrgyz(db, organization_kyrgyz):
    return UserFactory(username="regular_user", organization=organization_kyrgyz)


@pytest.fixture
def regular_user_uzbek(db, organization_uzbek):
    return UserFactory(username="regular_user", organization=organization_uzbek)


@pytest.fixture
def other_organization_user(db, backup_organization):
    return UserFactory(
        username="other_organization_user", user_role=User.UserRoles.REGULAR_USER, organization=backup_organization
    )


@pytest.fixture
def organization_admin(db, organization):
    return UserFactory(
        username="organization_admin", user_role=User.UserRoles.ORGANIZATION_ADMIN, organization=organization
    )


@pytest.fixture
def organization_admin_kyrgyz(db, organization_kyrgyz):
    return UserFactory(
        username="organization_admin", user_role=User.UserRoles.ORGANIZATION_ADMIN, organization=organization_kyrgyz
    )


@pytest.fixture
def organization_admin_uzbek(db, organization_uzbek):
    return UserFactory(
        username="organization_admin", user_role=User.UserRoles.ORGANIZATION_ADMIN, organization=organization_uzbek
    )


@pytest.fixture
def superadmin(db, organization):
    return UserFactory(username="superadmin", user_role=User.UserRoles.SUPER_ADMIN, organization=organization)


@pytest.fixture
def superadmin_kyrgyz(db, organization_kyrgyz):
    return UserFactory(username="superadmin", user_role=User.UserRoles.SUPER_ADMIN, organization=organization_kyrgyz)


@pytest.fixture
def superadmin_uzbek(db, organization_uzbek):
    return UserFactory(username="superadmin", user_role=User.UserRoles.SUPER_ADMIN, organization=organization_uzbek)


# api clients
@pytest.fixture
def api_client():
    return Client()


@pytest.fixture
def unauthenticated_api_client():
    return Client()


@pytest.fixture
def authenticated_regular_user_api_client(regular_user):
    return get_api_client_for_user(regular_user)


@pytest.fixture
def authenticated_regular_user_other_organization_api_client(other_organization_user):
    return get_api_client_for_user(other_organization_user)


@pytest.fixture
def regular_user_kyrgyz_api_client(regular_user_kyrgyz):
    return get_api_client_for_user(regular_user_kyrgyz)


@pytest.fixture
def regular_user_uzbek_api_client(regular_user_uzbek):
    return get_api_client_for_user(regular_user_uzbek)


@pytest.fixture
def authenticated_organization_user_api_client(organization_admin):
    return get_api_client_for_user(organization_admin)


@pytest.fixture
def organization_admin_kyrgyz_api_client(organization_admin_kyrgyz):
    return get_api_client_for_user(organization_admin_kyrgyz)


@pytest.fixture
def organization_admin_uzbek_api_client(organization_admin_uzbek):
    return get_api_client_for_user(organization_admin_uzbek)


@pytest.fixture
def authenticated_superadmin_user_api_client(superadmin):
    return get_api_client_for_user(superadmin)


@pytest.fixture
def superadmin_kyrgyz_api_client(superadmin_kyrgyz):
    return get_api_client_for_user(superadmin_kyrgyz)


@pytest.fixture
def superadmin_uzbek_api_client(superadmin_uzbek):
    return get_api_client_for_user(superadmin_uzbek)


# sites
@pytest.fixture
def site_one(db, organization):
    return SiteFactory(country="Kyrgyzstan", organization=organization)


@pytest.fixture
def site_two(db, backup_organization):
    return SiteFactory(country="Kazakhstan", organization=backup_organization)


@pytest.fixture
def site_kyrgyz(db, organization_kyrgyz):
    return SiteFactory(country="Kyrgyzstan", organization=organization_kyrgyz, timezone=ZoneInfo("Asia/Bishkek"))


@pytest.fixture
def site_kyrgyz_second(db, organization_kyrgyz):
    return SiteFactory(country="Kyrgyzstan", organization=organization_kyrgyz, timezone=ZoneInfo("Asia/Bishkek"))


@pytest.fixture
def site_kyrgyz_third(db, organization_kyrgyz):
    return SiteFactory(country="Kyrgyzstan", organization=organization_kyrgyz, timezone=ZoneInfo("Asia/Bishkek"))


@pytest.fixture
def site_uzbek(db, organization_uzbek):
    return SiteFactory(country="Uzbekistan", organization=organization_uzbek, timezone=ZoneInfo("Asia/Tashkent"))


# meteo stations


@pytest.fixture
def manual_meteo_station(db, site_one):
    return MeteorologicalStationFactory(site=site_one, station_code="12345", name="Manual Meteological Station")


@pytest.fixture
def manual_meteo_station_kyrgyz(db, site_kyrgyz):
    return MeteorologicalStationFactory(site=site_kyrgyz, station_code="12345", name="Manual Meteorological Station")


@pytest.fixture
def manual_second_meteo_station_kyrgyz(db, site_kyrgyz):
    return MeteorologicalStationFactory(
        site=site_kyrgyz, station_code="12346", name="Manual Meteorological Station number two"
    )


# hydro stations
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
def manual_second_hydro_station_kyrgyz(db, site_kyrgyz_second):
    return HydrologicalStationFactory(
        site=site_kyrgyz_second,
        station_type=HydrologicalStation.StationType.MANUAL,
        station_code="12346",
        name="Manual Kyrgyz Hydro Station number two",
    )


@pytest.fixture
def manual_third_hydro_station_kyrgyz(db, site_kyrgyz_third):
    return HydrologicalStationFactory(
        site=site_kyrgyz_third,
        station_type=HydrologicalStation.StationType.MANUAL,
        station_code="12347",
        name="Manual Kyrgyz Hydro Station number three",
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


# FileState
@pytest.fixture
def filestate_zks():
    return FileStateFactory(ingester_name="imomo_zks")


@pytest.fixture
def filestate_auto():
    return FileStateFactory(ingester_name="imomo_auto")
