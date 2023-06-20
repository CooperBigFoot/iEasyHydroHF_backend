import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from ninja_jwt.tokens import AccessToken

User = get_user_model()


@pytest.fixture
def regular_user(db, user_factory):
    return user_factory.create()


@pytest.fixture
def organization_admin(db, user_factory):
    return user_factory.create(user_role=User.UserRoles.ORGANIZATION_ADMIN)


@pytest.fixture
def superadmin(db, user_factory):
    return user_factory.create(user_role=User.UserRoles.SUPER_ADMIN)


@pytest.fixture
def api_client():
    return Client()


@pytest.fixture
def authenticated_regular_user_api_client(regular_user):
    token = AccessToken.for_user(regular_user)
    client = Client(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client
