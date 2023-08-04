import pytest
import pytz
from django.contrib.auth import get_user_model
from django.test import Client
from ninja_jwt.tokens import AccessToken

from sapphire_backend.organizations.models import Organization
from sapphire_backend.organizations.tests.factories import OrganizationFactory
from sapphire_backend.users.tests.factories import UserFactory

User = get_user_model()


@pytest.fixture
def regular_user(db, user_factory=UserFactory):
    return user_factory.create(username="regular_user")


@pytest.fixture
def organization(db, organization_factory=OrganizationFactory):
    return organization_factory.create(
        name="Kyrgyz Hydromet",
        language=Organization.Language.RUSSIAN,
        year_type=Organization.YearType.HYDROLOGICAL,
        timezone=pytz.timezone("Asia/Bishkek"),
    )


@pytest.fixture
def backup_organization(db, organization_factory=OrganizationFactory):
    return organization_factory.create(
        name="Kazalk Hydromet",
        language=Organization.Language.RUSSIAN,
        year_type=Organization.YearType.HYDROLOGICAL,
        timezone=pytz.timezone("Asia/Bishkek"),
    )


@pytest.fixture
def organization_admin(db, user_factory, organization):
    return user_factory.create(
        username="organization_admin", user_role=User.UserRoles.ORGANIZATION_ADMIN, organization=organization
    )


@pytest.fixture
def superadmin(db, user_factory):
    return user_factory.create(username="superadmin", user_role=User.UserRoles.SUPER_ADMIN)


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
