import pytest
from pytest_factoryboy import register

from .factories import (
    AirTemperatureFactory,
    WaterDischargeFactory,
    WaterLevelFactory,
    WaterTemperatureFactory,
    WaterVelocityFactory,
)

register(AirTemperatureFactory)
register(WaterDischargeFactory)
register(WaterLevelFactory)
register(WaterVelocityFactory)
register(WaterTemperatureFactory)


@pytest.fixture
def air_temperature_reading(db, air_temperature_factory=AirTemperatureFactory):
    return air_temperature_factory.create()
