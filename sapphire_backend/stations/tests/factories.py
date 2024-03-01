import factory
from faker import Faker
from zoneinfo import ZoneInfo

from sapphire_backend.organizations.tests.factories import BasinFactory, OrganizationFactory, RegionFactory

from ..models import HydrologicalStation, MeteorologicalStation, Site

fake = Faker()


class SiteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Site
        django_get_or_create = ()

    country = fake.country()
    organization = factory.SubFactory(OrganizationFactory)
    basin = factory.SubFactory(BasinFactory)
    region = factory.SubFactory(RegionFactory)

    timezone = ZoneInfo("UTC")

    latitude = fake.latitude()
    longitude = fake.longitude()
    elevation = fake.pyfloat(right_digits=1, min_value=0.0, max_value=5000)


class HydrologicalStationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = HydrologicalStation
        django_get_or_create = ("site", "station_type")

    site = factory.SubFactory(SiteFactory)
    description = fake.catch_phrase()
    station_type = HydrologicalStation.StationType.MANUAL
    station_code = fake.ean(length=8)


class MeteorologicalStationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MeteorologicalStation
        django_get_or_create = ("site",)

    site = factory.SubFactory(SiteFactory)
    description = fake.catch_phrase()
    station_code = fake.ean(length=8)
