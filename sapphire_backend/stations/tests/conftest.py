from datetime import datetime as dt
from zoneinfo import ZoneInfo

import pytest
from django.conf import settings
from pytest_factoryboy import register

from .factories import SensorFactory, StationFactory

register(SensorFactory)
register(StationFactory)


@pytest.fixture
def manual_station(db, station_factory):
    return station_factory.create(name="Manual station", is_automatic=False)


@pytest.fixture
def automatic_station(db, station_factory):
    return station_factory.create(name="Automatic station", is_automatic=True)


@pytest.fixture
def default_sensor(db, sensor_factory, automatic_station):
    return sensor_factory.create(
        name=f"Default sensor {automatic_station.name}",
        station=automatic_station,
        installation_date=dt(2022, 1, 1, tzinfo=ZoneInfo(settings.TIME_ZONE)),
    )


@pytest.fixture
def inactive_sensor(db, sensor_factory, automatic_station):
    return sensor_factory.create(name=f"Inactive sensor {automatic_station.name}", station=automatic_station)


@pytest.fixture
def extra_sensor(db, sensor_factory, automatic_station):
    return sensor_factory.create(
        name=f"Extra sensor {automatic_station.name}",
        station=automatic_station,
        installation_date=dt(2023, 1, 1, tzinfo=ZoneInfo(settings.TIME_ZONE)),
    )
