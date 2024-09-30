from datetime import datetime

import factory
from factory.django import DjangoModelFactory

from ..models import FileState


class FileStateFactory(DjangoModelFactory):
    class Meta:
        model = FileState

    filename = factory.Faker("file_name")
    remote_path = factory.Faker("file_path")
    local_path = factory.Faker("file_path")
    state_timestamp = factory.LazyFunction(datetime.now)
    ingester_name = factory.Faker("word")
    state = FileState.States.DISCOVERED
