import pytest
from datetime import datetime

from .factories import (
    OldDBFactory,
    OldSourceFactory,
    OldSiteFactory,
    OldDischargeModelFactory
)

@pytest.fixture
def old_db_session():
    """Create in-memory SQLite database session"""
    return OldDBFactory.create_session()

@pytest.fixture
def old_kyrgyz_source(old_db_session):
    """Create Kyrgyz Hydromet source"""
    return OldSourceFactory.create(old_db_session)

@pytest.fixture
def old_uzbek_source(old_db_session):
    """Create Uzbek Hydromet source"""
    return OldSourceFactory.create(
        old_db_session,
        organization="УзГидроМет",
        country="Uzbekistan",
        city="Tashkent"
    )

@pytest.fixture
def old_kyrgyz_station(old_db_session, old_kyrgyz_source):
    """Create a Kyrgyz station"""
    return OldSiteFactory.create(old_db_session, source=old_kyrgyz_source)

@pytest.fixture
def old_discharge_model(old_db_session, old_site):
    """Create a test discharge model in old DB"""
    return OldDischargeModelFactory.create(old_db_session, site=old_site)

@pytest.fixture
def clean_django_db():
    """Ensure clean Django test database"""
    from sapphire_backend.imomo.migrate_old_db import cleanup_all
    cleanup_all()
