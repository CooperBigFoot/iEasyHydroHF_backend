from datetime import datetime
from decimal import Decimal

import factory
from factory import SubFactory
from faker import Faker

from sapphire_backend.stations.tests.factories import HydrologicalStationFactory

from ..models import DischargeModel

fake = Faker()


class DischargeModelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DischargeModel
        django_get_or_create = ("name", "station", "param_a", "param_b", "param_c", "valid_from_local")

    name = fake.name()
    param_a = fake.pydecimal(left_digits=3, right_digits=2, positive=False, min_value=-100, max_value=100)
    param_b = Decimal("2.00")
    param_c = Decimal("0.0019")
    valid_from_local = datetime(2020, 1, 15)  # Fixed date of 2020-01-15
    station = SubFactory(HydrologicalStationFactory)
