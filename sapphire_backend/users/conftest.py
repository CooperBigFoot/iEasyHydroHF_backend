import pytest
from django.test import Client
from ninja_jwt.tokens import AccessToken
from pytest_factoryboy import register

from sapphire_backend.users.tests.factories import UserAssignedStationFactory, UserFactory

register(UserFactory)
register(UserAssignedStationFactory)


@pytest.fixture
def inactive_user(db, user_factory):
    return user_factory.create(
        first_name="Inactive",
        last_name="User",
        username="inactive_user",
        email="inactive@user.com",
        is_active=False,
        is_deleted=False,
    )


@pytest.fixture
def deleted_user(db, user_factory):
    return user_factory.create(
        first_name="Deleted",
        last_name="User",
        username="deleted_user",
        email="deleted@user.com",
        is_active=False,
        is_deleted=True,
    )


@pytest.fixture
def user_without_first_last_name(db, user_factory):
    return user_factory.create(first_name="", last_name="", username="my_display_name", email="display@name.com")


@pytest.fixture
def user_with_only_first_name(db, user_factory):
    return user_factory.create(first_name="First", last_name="", username="my_display_name", email="display@name.com")


@pytest.fixture
def user_with_only_last_name(db, user_factory):
    return user_factory.create(first_name="", last_name="Last", username="my_display_name", email="display@name.com")


def get_api_client_for_user(user):
    token = AccessToken.for_user(user)
    client = Client(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def regular_user_assigned_hydro_station(db, regular_user, manual_hydro_station):
    return UserAssignedStationFactory(
        user=regular_user,
        hydro_station=manual_hydro_station,
        meteo_station=None,
        virtual_station=None,
        assigned_by=None,
    )


@pytest.fixture
def regular_user_assigned_meteo_station(db, regular_user, manual_meteo_station):
    return UserAssignedStationFactory(
        user=regular_user, hydro_station=None, meteo_station=manual_meteo_station, virtual_station=None
    )


@pytest.fixture
def regular_user_assigned_virtual_station(db, regular_user_kyrgyz, virtual_station_kyrgyz):
    return UserAssignedStationFactory(
        user=regular_user_kyrgyz, hydro_station=None, meteo_station=None, virtual_station=virtual_station_kyrgyz
    )
