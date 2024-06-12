from decimal import Decimal

import pytest
from pytest_factoryboy import register

from sapphire_backend.estimations.tests.factories import DischargeModelFactory
from sapphire_backend.metrics.choices import NormType
from sapphire_backend.metrics.tests.factories import DischargeNormFactory
from sapphire_backend.stations.tests.factories import (
    VirtualStationAssociationFactory,
    VirtualStationFactory,
)

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
def discharge_model_manual_hydro_station_kyrgyz(db, manual_hydro_station_kyrgyz):
    return DischargeModelFactory(
        name="Discharge model station 1", param_a=-30, param_c=0.007, station=manual_hydro_station_kyrgyz
    )


@pytest.fixture
def discharge_model_manual_second_hydro_station_kyrgyz(db, manual_second_hydro_station_kyrgyz):
    return DischargeModelFactory(
        name="Discharge model station 2", param_a=51, param_c=0.0017, station=manual_second_hydro_station_kyrgyz
    )


@pytest.fixture
def discharge_model_manual_third_hydro_station_kyrgyz(db, manual_third_hydro_station_kyrgyz):
    return DischargeModelFactory(
        name="Discharge model station 3", param_a=30, param_c=0.0036, station=manual_third_hydro_station_kyrgyz
    )


@pytest.fixture
def decadal_discharge_norm_manual_hydro_station_kyrgyz(db, manual_hydro_station_kyrgyz):
    return DischargeNormFactory(
        station=manual_hydro_station_kyrgyz, value=Decimal(10.1), norm_type=NormType.DECADAL, ordinal_number=1
    )


@pytest.fixture
def decadal_discharge_norm_manual_second_hydro_station_kyrgyz(db, manual_second_hydro_station_kyrgyz):
    return DischargeNormFactory(
        station=manual_second_hydro_station_kyrgyz, value=Decimal(20.54), norm_type=NormType.DECADAL, ordinal_number=1
    )


@pytest.fixture
def decadal_discharge_norm_manual_third_hydro_station_kyrgyz(db, manual_third_hydro_station_kyrgyz):
    return DischargeNormFactory(
        station=manual_third_hydro_station_kyrgyz, value=Decimal(70.44), norm_type=NormType.DECADAL, ordinal_number=1
    )


@pytest.fixture
def monthly_discharge_norm_manual_hydro_station_kyrgyz(db, manual_hydro_station_kyrgyz):
    return DischargeNormFactory(
        station=manual_hydro_station_kyrgyz, value=Decimal(10.7), norm_type=NormType.MONTHLY, ordinal_number=1
    )


@pytest.fixture
def monthly_discharge_norm_manual_second_hydro_station_kyrgyz(db, manual_second_hydro_station_kyrgyz):
    return DischargeNormFactory(
        station=manual_second_hydro_station_kyrgyz, value=Decimal(15.0), norm_type=NormType.MONTHLY, ordinal_number=1
    )
