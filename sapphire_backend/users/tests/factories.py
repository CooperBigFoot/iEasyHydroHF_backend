import factory
from django.contrib.auth import get_user_model
from django.db.models import signals
from faker import Faker
from zoneinfo import ZoneInfo

from sapphire_backend.organizations.tests.factories import OrganizationFactory
from sapphire_backend.stations.tests.factories import (
    HydrologicalStationFactory,
    MeteorologicalStationFactory,
    VirtualStationFactory,
)
from sapphire_backend.users.models import UserAssignedStation

User = get_user_model()

fake = Faker()


@factory.django.mute_signals(signals.post_save, signals.post_delete)
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("username", "organization")

    first_name = fake.first_name()
    last_name = fake.last_name()

    email = fake.ascii_email()
    username = fake.language_name()
    password = factory.PostGenerationMethodCall("set_password", "password123")

    is_active = True
    date_joined = fake.date_time_between(start_date="-1y", tzinfo=ZoneInfo("UTC"))

    contact_phone = fake.phone_number()
    user_role = User.UserRoles.REGULAR_USER

    organization = factory.SubFactory(OrganizationFactory)


class UserAssignedStationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserAssignedStation
        django_get_or_create = ("user", "hydro_station", "meteo_station", "virtual_station")

    user = factory.SubFactory(UserFactory)
    hydro_station = factory.SubFactory(HydrologicalStationFactory)
    meteo_station = factory.SubFactory(MeteorologicalStationFactory)
    virtual_station = factory.SubFactory(VirtualStationFactory)
    assigned_by = factory.SubFactory(UserFactory)
