import factory
from faker import Faker
from zoneinfo import ZoneInfo

from sapphire_backend.organizations.tests.factories import BasinFactory, OrganizationFactory, RegionFactory

from ..models import HydrologicalStation, MeteorologicalStation, Site, VirtualStation, VirtualStationAssociation

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
        django_get_or_create = "site"

    site = factory.SubFactory(SiteFactory)
    description = fake.catch_phrase()
    station_code = fake.ean(length=8)


class VirtualStationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = VirtualStation
        django_get_or_create = ("organization", "station_code")

    country = fake.country()
    organization = factory.SubFactory(OrganizationFactory)
    basin = factory.SubFactory(BasinFactory)
    region = factory.SubFactory(RegionFactory)

    timezone = ZoneInfo("UTC")

    latitude = fake.latitude()
    longitude = fake.longitude()
    elevation = fake.pyfloat(right_digits=1, min_value=0.0, max_value=5000)

    name = fake.company()
    description = fake.catch_phrase()
    station_code = fake.ean(length=8)
    is_deleted = False


class VirtualStationAssociationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = VirtualStationAssociation
        django_get_or_create = ("virtual_station", "hydro_station")

    virtual_station = factory.SubFactory(VirtualStationFactory)
    hydro_station = factory.SubFactory(HydrologicalStationFactory)
    weight = fake.pyfloat(right_digits=1, min_value=0.0, max_value=100.0)
