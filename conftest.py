import pytest
from django.test import Client
from ninja_jwt.tokens import RefreshToken


@pytest.fixture
def regular_user(db, user_factory):
    return user_factory.create()


@pytest.fixture
def api_client():
    return Client()


@pytest.fixture
def authenticated_api_client(regular_user):
    token = RefreshToken.for_user(regular_user)
    client = Client()
    print(token)
    return client
