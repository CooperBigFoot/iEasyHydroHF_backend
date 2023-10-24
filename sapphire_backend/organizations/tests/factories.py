import factory
from faker import Faker
from zoneinfo import ZoneInfo

from ..models import Organization

fake = Faker()


class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization
        django_get_or_create = ("name",)

    name = fake.company()
    description = fake.catch_phrase()
    url = fake.domain_name()
    uuid = fake.uuid4()

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
