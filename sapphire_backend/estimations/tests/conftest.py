import random
from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from pytest_factoryboy import register
from zoneinfo import ZoneInfo

from sapphire_backend.estimations.tests.factories import DischargeModelFactory
from sapphire_backend.metrics.choices import HydrologicalMeasurementType, HydrologicalMetricName, MetricUnit, NormType
from sapphire_backend.metrics.tests.factories import HydrologicalMetricFactory, HydrologicalNormFactory
from sapphire_backend.stations.models import HydrologicalStation
from sapphire_backend.stations.tests.factories import (
    VirtualStationAssociationFactory,
    VirtualStationFactory,
)
from sapphire_backend.utils.datetime_helper import DateRange, SmartDatetime
from sapphire_backend.utils.db_helper import refresh_continuous_aggregate
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
def discharge_model_manual_hydro_station_kyrgyz(db, manual_hydro_station_kyrgyz):
    return DischargeModelFactory(
        name="Discharge model station 1",
        param_a=-30,
        param_c=0.007,
        valid_from_local=datetime(2020, 1, 15, tzinfo=ZoneInfo("UTC")),  # must be 2020-01-15
        station=manual_hydro_station_kyrgyz,
    )


@pytest.fixture
def discharge_second_model_manual_hydro_station_kyrgyz(db, manual_hydro_station_kyrgyz):
    return DischargeModelFactory(
        name="Second discharge model station 1",
        param_a=20,
        param_c=0.003,
        valid_from_local=datetime(2020, 3, 1, tzinfo=ZoneInfo("UTC")),  # must be 2020-03-01
        station=manual_hydro_station_kyrgyz,
    )


@pytest.fixture
def discharge_model_manual_second_hydro_station_kyrgyz(db, manual_second_hydro_station_kyrgyz):
    return DischargeModelFactory(
        name="Discharge model station 2",
        param_a=51,
        param_c=0.0017,
        valid_from_local=datetime(2020, 1, 15),
        station=manual_second_hydro_station_kyrgyz,
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


def generate_water_level_daily_metrics(start_date: date, end_date: date, station: HydrologicalStation):
    metrics = []
    for current_date in DateRange(start_date, end_date, timedelta(days=1)):
        smart_dt = SmartDatetime(current_date, station=station, tz_included=False)
        wl_morning = HydrologicalMetricFactory(
            timestamp=smart_dt.morning_tz,
            station=station,
            avg_value=random.randint(50, 250),
            value_type=HydrologicalMeasurementType.MANUAL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            unit=MetricUnit.WATER_LEVEL,
        )
        wl_evening = HydrologicalMetricFactory(
            timestamp=smart_dt.evening_tz,
            station=station,
            avg_value=int(wl_morning.avg_value) + random.randint(-30, 30),
            value_type=HydrologicalMeasurementType.MANUAL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            unit=MetricUnit.WATER_LEVEL,
        )
        metrics.append((wl_morning, wl_evening))
    refresh_continuous_aggregate()
    return metrics


@pytest.fixture
def water_level_metrics_daily_generator(request, manual_hydro_station_kyrgyz):
    start_date, end_date = request.param
    return generate_water_level_daily_metrics(start_date, end_date, manual_hydro_station_kyrgyz)


@pytest.fixture
def water_level_metrics_daily_generator_second_station(request, manual_second_hydro_station_kyrgyz):
    start_date, end_date = request.param
    return generate_water_level_daily_metrics(start_date, end_date, manual_second_hydro_station_kyrgyz)
