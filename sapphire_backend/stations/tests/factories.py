import factory
import pytz
from faker import Faker

from sapphire_backend.organizations.tests.factories import OrganizationFactory

from ..models import Station

fake = Faker()


class StationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Station
        django_get_or_create = ("name",)

    name = fake.company()
    description = fake.catch_phrase()
    station_type = Station.StationType.HYDROLOGICAL

    organization = factory.SubFactory(OrganizationFactory)
    station_code = fake.ean(length=8)

    country = fake.country()
    basin = fake.city()
    region = fake.city()
    timezone = pytz.UTC

    latitude = fake.latitude()
    longitude = fake.longitude()
    elevation = fake.pyfloat(right_digits=1, positive=True, min_value=0.0, max_value=5000)

    is_automatic = False
    is_deleted = False
    is_virtual = False

    measurement_time_step = fake.pyint(min_value=1, max_value=720)
    discharge_level_alarm = 100
