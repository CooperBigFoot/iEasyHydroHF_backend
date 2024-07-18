import factory
from factory.django import DjangoModelFactory

from sapphire_backend.ingestion.tests.factories import FileStateFactory
from sapphire_backend.organizations.tests.factories import OrganizationFactory
from sapphire_backend.telegrams.models import TelegramReceived


class TelegramReceivedFactory(DjangoModelFactory):
    class Meta:
        model = TelegramReceived

    created_date = None
    telegram = factory.Faker("text")
    valid = True
    station_code = factory.Faker("bothify", text="ST##")
    decoded_values = {}
    errors = ""
    acknowledged = False
    acknowledged_ts = None
    acknowledged_by = None
    filestate = factory.SubFactory(FileStateFactory)
    auto_stored = False
    organization = factory.SubFactory(OrganizationFactory)
