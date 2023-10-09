from zoneinfo import ZoneInfo

import factory
from faker import Faker

from sapphire_backend.stations.tests.factories import SensorFactory

from ..models import AirTemperature, Precipitation, WaterDischarge, WaterLevel, WaterTemperature, WaterVelocity

fake = Faker()


class MetricFactoryMixin(factory.django.DjangoModelFactory):
    timestamp = fake.date_time(tzinfo=ZoneInfo("UTC"))
    sensor = factory.SubFactory(SensorFactory)


class AirTemperatureFactory(MetricFactoryMixin):
    value = fake.pydecimal(left_digits=2, right_digits=6, min_value=0, max_value=45)
    unit = "°C"

    class Meta:
        model = AirTemperature
        django_get_or_create = ("timestamp", "sensor")


class PrecipitationFactory(MetricFactoryMixin):
    value = fake.pydecimal(left_digits=2, right_digits=6, min_value=0, max_value=20)
    unit = "mm"

    class Meta:
        model = Precipitation
        django_get_or_create = ("timestamp", "sensor")


class WaterTemperatureFactory(MetricFactoryMixin):
    value = fake.pydecimal(left_digits=2, right_digits=6, min_value=0, max_value=28)
    unit = "°C"

    class Meta:
        model = WaterTemperature
        django_get_or_create = ("timestamp", "sensor")


class WaterDischargeFactory(MetricFactoryMixin):
    value = fake.pydecimal(left_digits=3, right_digits=6, min_value=0, max_value=1000)
    unit = "m³/s"

    class Meta:
        model = WaterDischarge
        django_get_or_create = ("timestamp", "sensor")


class WaterVelocityFactory(MetricFactoryMixin):
    value = fake.pydecimal(left_digits=1, right_digits=6, min_value=1, max_value=4)
    unit = "m/s"

    class Meta:
        model = WaterVelocity
        django_get_or_create = ("timestamp", "sensor")


class WaterLevelFactory(MetricFactoryMixin):
    value = fake.pydecimal(left_digits=2, right_digits=6, min_value=1, max_value=20)
    unit = "m"

    class Meta:
        model = WaterLevel
        django_get_or_create = ("timestamp", "sensor")
