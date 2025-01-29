from datetime import datetime
from decimal import Decimal

import pytest
from pytest_factoryboy import register
from zoneinfo import ZoneInfo

from sapphire_backend.estimations.models import DischargeModel
from sapphire_backend.estimations.tests.factories import DischargeModelFactory
from sapphire_backend.metrics.choices import NormType
from sapphire_backend.metrics.tests.factories import HydrologicalNormFactory
from sapphire_backend.stations.tests.factories import (
    VirtualStationAssociationFactory,
    VirtualStationFactory,
)
from sapphire_backend.utils.rounding import hydrological_round

register(VirtualStationFactory)
register(VirtualStationAssociationFactory)


@pytest.fixture
def virtual_station(db, organization_kyrgyz):
    return VirtualStationFactory(
        name="Virtual Station Main", organization=organization_kyrgyz, station_code="77777", longitude=None
    )


@pytest.fixture
def virtual_station_association_one(db, manual_hydro_station_kyrgyz, virtual_station):
    return VirtualStationAssociationFactory(
        virtual_station=virtual_station, hydro_station=manual_hydro_station_kyrgyz, weight=50
    )


@pytest.fixture
def virtual_station_association_two(db, manual_second_hydro_station_kyrgyz, virtual_station):
    return VirtualStationAssociationFactory(
        virtual_station=virtual_station, hydro_station=manual_second_hydro_station_kyrgyz, weight=70
    )


@pytest.fixture
def virtual_station_association_three(db, manual_third_hydro_station_kyrgyz, virtual_station):
    return VirtualStationAssociationFactory(
        virtual_station=virtual_station, hydro_station=manual_third_hydro_station_kyrgyz, weight=43
    )


@pytest.fixture
def discharge_model_manual_third_hydro_station_kyrgyz(db, manual_third_hydro_station_kyrgyz):
    return DischargeModelFactory(
        name="Discharge model station 3",
        param_a=30,
        param_c=0.0036,
        valid_from_local=datetime(2020, 1, 15),
        station=manual_third_hydro_station_kyrgyz,
    )


@pytest.fixture
def decadal_discharge_norm_manual_hydro_station_kyrgyz(db, manual_hydro_station_kyrgyz):
    return HydrologicalNormFactory(
        station=manual_hydro_station_kyrgyz,
        value=hydrological_round(Decimal("10.1")),
        norm_type=NormType.DECADAL,
        ordinal_number=1,
    )


@pytest.fixture
def decadal_discharge_norm_manual_second_hydro_station_kyrgyz(db, manual_second_hydro_station_kyrgyz):
    return HydrologicalNormFactory(
        station=manual_second_hydro_station_kyrgyz,
        value=hydrological_round(Decimal("20.54")),
        norm_type=NormType.DECADAL,
        ordinal_number=1,
    )


@pytest.fixture
def decadal_discharge_norm_manual_third_hydro_station_kyrgyz(db, manual_third_hydro_station_kyrgyz):
    return HydrologicalNormFactory(
        station=manual_third_hydro_station_kyrgyz,
        value=hydrological_round(Decimal("70.44")),
        norm_type=NormType.DECADAL,
        ordinal_number=1,
    )


@pytest.fixture
def monthly_discharge_norm_manual_hydro_station_kyrgyz(db, manual_hydro_station_kyrgyz):
    return HydrologicalNormFactory(
        station=manual_hydro_station_kyrgyz,
        value=hydrological_round(Decimal("10.7")),
        norm_type=NormType.MONTHLY,
        ordinal_number=1,
    )


@pytest.fixture
def monthly_discharge_norm_manual_second_hydro_station_kyrgyz(db, manual_second_hydro_station_kyrgyz):
    return HydrologicalNormFactory(
        station=manual_second_hydro_station_kyrgyz,
        value=hydrological_round(Decimal(15.0)),
        norm_type=NormType.MONTHLY,
        ordinal_number=1,
    )


@pytest.fixture
def discharge_model_2023(db, manual_hydro_station_kyrgyz):
    return DischargeModel.objects.create(
        name="Latest Model",
        valid_from_local=datetime(2023, 1, 1, tzinfo=ZoneInfo("UTC")),
        param_a=10,
        param_b=2,
        param_c=0.0005,
        station=manual_hydro_station_kyrgyz,
    )


@pytest.fixture
def discharge_model_2021(db, manual_hydro_station_kyrgyz):
    return DischargeModel.objects.create(
        name="Discharge model 2021",
        valid_from_local=datetime(2021, 1, 1, tzinfo=ZoneInfo("UTC")),
        param_a=10,
        param_b=2,
        param_c=0.0005,
        station=manual_hydro_station_kyrgyz,
    )
