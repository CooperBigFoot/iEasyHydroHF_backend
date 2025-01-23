import pytest
from datetime import datetime

from .factories import (
    OldDBFactory,
    OldSourceFactory,
    OldSiteFactory,
    OldDischargeModelFactory,
    DataValueFactory
)
from sapphire_backend.organizations.models import Organization
from sapphire_backend.stations.models import HydrologicalStation
from sapphire_backend.stations.tests.factories import (
    OrganizationFactory,
    BasinFactory,
    RegionFactory,
    SiteFactory,
    HydrologicalStationFactory,
)
from sapphire_backend.imomo.data_structs.standard_data import Variables

@pytest.fixture
def old_db_session():
    """Create in-memory SQLite database session"""
    return OldDBFactory.create_session()

@pytest.fixture
def old_kyrgyz_source(old_db_session):
    """Create Kyrgyz Hydromet source"""
    return OldSourceFactory.create(
        old_db_session,
        organization="КыргызГидроМет",
        year_type="hydro_year",
        language="ru",
        country="Kyrgyzstan",
        city="Bishkek",
        address="Test Address KG",
        zip_code="720000",
        email="test.kg@example.com",
        contact_name="Test Contact KG",
        phone="996123456789"
    )

@pytest.fixture
def old_uzbek_source(old_db_session):
    """Create Uzbek Hydromet source"""
    return OldSourceFactory.create(
        old_db_session,
        organization="УзГидроМет",
        year_type="hydro_year",
        language="ru",
        country="Uzbekistan",
        city="Tashkent",
        address="Test Address UZ",
        zip_code="100000",  # Tashkent zip code
        email="test.uz@example.com",
        contact_name="Test Contact UZ",
        phone="998123456789"
    )

@pytest.fixture
def old_kyrgyz_station_first(old_db_session, old_kyrgyz_source):
    """Create first Kyrgyz station"""
    return OldSiteFactory.create(
        old_db_session,
        source=old_kyrgyz_source,
        site_code="1234",
        site_name="Kyrgyz Station First",
        latitude=42.8746,  # Bishkek latitude
        longitude=74.5698,  # Bishkek longitude
        country="Kyrgyzstan",
        basin="Нарын",
        region="ЖАЛАЛ-АБАДСКАЯ ОБЛАСТЬ"
    )

@pytest.fixture
def old_kyrgyz_station_second(old_db_session, old_kyrgyz_source):
    """Create second Kyrgyz station"""
    return OldSiteFactory.create(
        old_db_session,
        source=old_kyrgyz_source,
        site_code="5678",
        site_name="Kyrgyz Station Second",
        latitude=42.8746,
        longitude=74.5698,
        country="Kyrgyzstan",
        basin="Нарын",
        region="ЖАЛАЛ-АБАДСКАЯ ОБЛАСТЬ"
    )

@pytest.fixture
def old_uzbek_station_first(old_db_session, old_uzbek_source):
    """Create first Uzbek station"""
    return OldSiteFactory.create(
        old_db_session,
        source=old_uzbek_source,
        site_code="9012",
        site_name="Uzbek Station First",
        latitude=41.2995,  # Tashkent latitude
        longitude=69.2401,  # Tashkent longitude
        country="Uzbekistan",
        basin="Сырдарья",
        region="ТАШКЕНТСКАЯ ОБЛАСТЬ"
    )

@pytest.fixture
def old_uzbek_station_second(old_db_session, old_uzbek_source):
    """Create second Uzbek station"""
    return OldSiteFactory.create(
        old_db_session,
        source=old_uzbek_source,
        site_code="3456",
        site_name="Uzbek Station Second",
        latitude=41.2995,
        longitude=69.2401,
        country="Uzbekistan",
        basin="Сырдарья",
        region="ТАШКЕНТСКАЯ ОБЛАСТЬ"
    )

@pytest.fixture
def old_kyrgyz_discharge_model_first(old_db_session, old_kyrgyz_station_first):
    """Create discharge model for first Kyrgyz station"""
    return OldDischargeModelFactory.create(
        old_db_session,
        site=old_kyrgyz_station_first,
        model_name="Kyrgyz Model First"
    )

@pytest.fixture
def old_kyrgyz_discharge_model_second(old_db_session, old_kyrgyz_station_second):
    """Create discharge model for second Kyrgyz station"""
    return OldDischargeModelFactory.create(
        old_db_session,
        site=old_kyrgyz_station_second,
        model_name="Kyrgyz Model Second"
    )

@pytest.fixture
def old_uzbek_discharge_model_first(old_db_session, old_uzbek_station_first):
    """Create discharge model for first Uzbek station"""
    return OldDischargeModelFactory.create(
        old_db_session,
        site=old_uzbek_station_first,
        model_name="Uzbek Model First"
    )

@pytest.fixture
def old_uzbek_discharge_model_second(old_db_session, old_uzbek_station_second):
    """Create discharge model for second Uzbek station"""
    return OldDischargeModelFactory.create(
        old_db_session,
        site=old_uzbek_station_second,
        model_name="Uzbek Model Second"
    )

@pytest.fixture
def old_water_level_value(old_db_session, old_kyrgyz_station_first):
    """Create water level observation in old DB"""
    return DataValueFactory.create(
        old_db_session,
        site=old_kyrgyz_station_first,
        data_value=123.45,
        local_date_time=datetime(2023, 1, 1, 8, 0),
        variable__variable_code=Variables.gauge_height_daily_measurement.value
    )

@pytest.fixture
def clean_django_db():
    """Ensure clean Django test database"""
    from sapphire_backend.imomo.migrate_old_db import cleanup_all
    cleanup_all()

@pytest.fixture
def existing_kyrgyz_org():
    """Create Kyrgyz Hydromet organization in new DB"""
    return OrganizationFactory(
        name="КыргызГидроМет",
        language=Organization.Language.RUSSIAN
    )

@pytest.fixture
def existing_kyrgyz_basin(existing_kyrgyz_org):
    """Create Naryn basin in new DB"""
    return BasinFactory(
        name="Нарын",
        organization=existing_kyrgyz_org
    )

@pytest.fixture
def existing_kyrgyz_region(existing_kyrgyz_org):
    """Create Jalal-Abad region in new DB"""
    return RegionFactory(
        name="ЖАЛАЛ-АБАДСКАЯ ОБЛАСТЬ",
        organization=existing_kyrgyz_org
    )

@pytest.fixture
def existing_kyrgyz_site(existing_kyrgyz_org, existing_kyrgyz_basin, existing_kyrgyz_region):
    """Create Kyrgyz site in new DB"""
    return SiteFactory(
        organization=existing_kyrgyz_org,
        basin=existing_kyrgyz_basin,
        region=existing_kyrgyz_region,
        country="Kyrgyzstan",
        latitude=42.8746,
        longitude=74.5698
    )

@pytest.fixture
def existing_kyrgyz_station(existing_kyrgyz_site):
    """Create Kyrgyz station in new DB"""
    return HydrologicalStationFactory(
        name="Kyrgyz Station First",
        station_code="1234",
        station_type=HydrologicalStation.StationType.MANUAL,
        site=existing_kyrgyz_site
    )

@pytest.fixture
def existing_kyrgyz_station_second(existing_kyrgyz_site):
    """Create second Kyrgyz station in new DB"""
    return HydrologicalStationFactory(
        name="Kyrgyz Station Second",
        station_code="5678",
        station_type=HydrologicalStation.StationType.MANUAL,
        site=existing_kyrgyz_site
    )
