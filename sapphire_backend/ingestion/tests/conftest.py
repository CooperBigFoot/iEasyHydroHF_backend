import pytest

from sapphire_backend.ingestion.tests.factories import FileStateFactory


@pytest.fixture
def filestate_zks():
    return FileStateFactory(ingester_name="imomo_zks")


@pytest.fixture
def filestate_auto():
    return FileStateFactory(ingester_name="imomo_auto")
