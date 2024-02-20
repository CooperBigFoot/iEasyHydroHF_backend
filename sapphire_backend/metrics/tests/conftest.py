import datetime as dt

import pytest
from pytest_factoryboy import register

from sapphire_backend.metrics.choices import HydrologicalMeasurementType, HydrologicalMetricName, MetricUnit

from .factories import HydrologicalMetricFactory, MeteorologicalMetricFactory

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
