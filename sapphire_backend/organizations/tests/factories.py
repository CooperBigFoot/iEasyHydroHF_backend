import factory
import pytz
from faker import Faker

from ..models import Organization

fake = Faker()


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
    timezone = pytz.UTC

    year_type = Organization.YearType.CALENDAR
    language = Organization.Language.ENGLISH

    is_active = True
