import factory
from faker import Faker
from zoneinfo import ZoneInfo

from ..models import Basin, Organization, Region

fake = Faker("ru_RU")


class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization
        django_get_or_create = ("name",)

    name = fake.company()
    description = fake.catch_phrase()
    url = fake.domain_name()

    country = fake.country()
    city = fake.city()
    street_address = fake.street_address()
    zip_code = fake.postcode()

    contact = fake.name()
    contact_phone = fake.phone_number()
    timezone = ZoneInfo("UTC")

    year_type = Organization.YearType.CALENDAR
    language = Organization.Language.ENGLISH

    is_active = True


class BasinFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Basin
        django_get_or_create = ("name",)

    name = fake.region()
    organization = factory.SubFactory(OrganizationFactory)


class RegionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Region
        django_get_or_create = ("name",)

    name = fake.region()
    organization = factory.SubFactory(OrganizationFactory)
