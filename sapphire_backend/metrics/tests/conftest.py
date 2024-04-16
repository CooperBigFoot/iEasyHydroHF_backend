import datetime as dt

import pytest
from pytest_factoryboy import register

from sapphire_backend.metrics.choices import HydrologicalMeasurementType, HydrologicalMetricName, MetricUnit, NormType

from .factories import DischargeNormFactory, HydrologicalMetricFactory, MeteorologicalMetricFactory

register(DischargeNormFactory)
register(HydrologicalMetricFactory)
register(MeteorologicalMetricFactory)

# order of the hydro metrics from latest to oldest
# water_discharge, water_level_manual_other, water_level_automatic, water_level_manual


@pytest.fixture
def water_level_manual(db, manual_hydro_station):
    # oldest
    return HydrologicalMetricFactory(
        timestamp=dt.datetime.now(tz=dt.timezone.utc) - dt.timedelta(days=3),
        station=manual_hydro_station,
        avg_value=10.0,
        value_type=HydrologicalMeasurementType.MANUAL,
        metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
        unit=MetricUnit.WATER_LEVEL,
    )


@pytest.fixture
def water_discharge(db, manual_hydro_station):
    # latest
    return HydrologicalMetricFactory(
        timestamp=dt.datetime.now(tz=dt.timezone.utc),
        station=manual_hydro_station,
        avg_value=2.0,
        value_type=HydrologicalMeasurementType.ESTIMATED,
        metric_name=HydrologicalMetricName.WATER_DISCHARGE_DAILY,
        unit=MetricUnit.WATER_DISCHARGE,
    )


@pytest.fixture
def water_level_manual_other(db, manual_hydro_station):
    return HydrologicalMetricFactory(
        station=manual_hydro_station,
        timestamp=dt.datetime.now(tz=dt.timezone.utc) - dt.timedelta(days=1),
        avg_value=10.0,
        value_type=HydrologicalMeasurementType.MANUAL,
        metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
        unit=MetricUnit.WATER_LEVEL,
    )


@pytest.fixture
def water_level_automatic(db, automatic_hydro_station):
    return HydrologicalMetricFactory(
        station=automatic_hydro_station,
        timestamp=dt.datetime.now(tz=dt.timezone.utc) - dt.timedelta(days=2),
        avg_value=9.8,
        value_type=HydrologicalMeasurementType.AUTOMATIC,
        metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
        unit=MetricUnit.WATER_LEVEL,
    )


@pytest.fixture
def water_level_manual_other_organization(db, manual_hydro_station_other_organization):
    return HydrologicalMetricFactory(
        station=manual_hydro_station_other_organization,
        timestamp=dt.datetime.now(tz=dt.timezone.utc) + dt.timedelta(minutes=10),
        avg_value=10.0,
        value_type=HydrologicalMeasurementType.MANUAL,
        metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
        unit=MetricUnit.WATER_LEVEL,
    )


@pytest.fixture
def decadal_discharge_norm_first(db, manual_hydro_station):
    return DischargeNormFactory(station=manual_hydro_station, value=1.0, norm_type=NormType.DECADAL, ordinal_number=1)


@pytest.fixture
def decadal_discharge_norm_second(db, manual_hydro_station):
    return DischargeNormFactory(station=manual_hydro_station, value=2.0, norm_type=NormType.DECADAL, ordinal_number=2)


@pytest.fixture
def monthly_discharge_norm_first(db, manual_hydro_station):
    return DischargeNormFactory(station=manual_hydro_station, value=1.0, norm_type=NormType.MONTHLY, ordinal_number=1)


@pytest.fixture
def monthly_discharge_norm_second(db, manual_hydro_station):
    return DischargeNormFactory(station=manual_hydro_station, value=2.0, norm_type=NormType.MONTHLY, ordinal_number=2)
