import pytest
from django.contrib.auth import get_user_model
from pytest_factoryboy import register

from sapphire_backend.users.tests.factories import UserFactory

User = get_user_model()

register(UserFactory)


@pytest.fixture
def organization_admin(db, user_factory):
    return user_factory.create(user_role=User.UserRoles.ORGANIZATION_ADMIN)


@pytest.fixture
def superadmin(db, user_factory):
    return user_factory.create(user_role=User.UserRoles.SUPER_ADMIN)


@pytest.fixture
def inactive_user(db, user_factory):
    return user_factory.create(
        first_name="Deleted", last_name="User", username="deleted_user", email="delete@user.com", is_active=False
    )
