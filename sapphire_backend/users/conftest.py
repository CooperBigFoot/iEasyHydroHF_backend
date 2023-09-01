import pytest
from pytest_factoryboy import register

from sapphire_backend.users.tests.factories import UserFactory

register(UserFactory)


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
