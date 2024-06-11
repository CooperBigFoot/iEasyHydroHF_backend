import pytest
from pytest_factoryboy import register

from sapphire_backend.estimations.tests.factories import DischargeModelFactory
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
def discharge_model_manual_hydro_station_kyrgyz(db, manual_hydro_station_kyrgyz):
    return DischargeModelFactory(
        name="Discharge model station 1", param_a=-30, param_c=0.007, station=manual_hydro_station_kyrgyz
    )


@pytest.fixture
def discharge_model_manual_second_hydro_station_kyrgyz(db, manual_second_hydro_station_kyrgyz):
    return DischargeModelFactory(
        name="Discharge model station 2", param_a=51, param_c=0.0017, station=manual_second_hydro_station_kyrgyz
    )
