import factory
from faker import Faker
from zoneinfo import ZoneInfo

from sapphire_backend.stations.tests.factories import HydrologicalStationFactory, MeteorologicalStationFactory

from ..models import HydrologicalMetric, MeteorologicalMetric

fake = Faker()


class HydrologicalMetricFactory(factory.django.DjangoModelFactory):
    timestamp = fake.date_time(tzinfo=ZoneInfo("UTC"))
    station = factory.SubFactory(HydrologicalStationFactory)
    min_value = fake.pydecimal(left_digits=2, right_digits=6, min_value=0, max_value=10)
    avg_value = fake.pydecimal(left_digits=2, right_digits=6, min_value=10, max_value=20)
    max_value = fake.pydecimal(left_digits=2, right_digits=6, min_value=20, max_value=30)
    value_type = HydrologicalMetric.MeasurementType.UNKNOWN
    metric_name = HydrologicalMetric.MetricName.WATER_LEVEL
    sensor_identifier = fake.ean(length=8)
    sensor_type = fake.color_name()
    unit = ""

    class Meta:
        model = HydrologicalMetric
        django_get_or_create = ("timestamp", "station_id", "sensor_identifier", "metric_name")


class MeteorologicalMetricFactory(factory.django.DjangoModelFactory):
    timestamp = fake.date_time(tzinfo=ZoneInfo("UTC"))
    value = fake.pydecimal(left_digits=2, right_digits=6, min_value=10, max_value=20)
    station = factory.SubFactory(MeteorologicalStationFactory)
    metric_name = MeteorologicalMetric.MetricName.AIR_TEMPERATURE
    value_type = MeteorologicalMetric.MeasurementType.UNKNOWN
    unit = ""

    class Meta:
        model = MeteorologicalMetric
        django_get_or_create = ("timestamp", "station_id", "metric_name")
