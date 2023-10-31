from django.db.models.aggregates import Avg, Max, Min

from sapphire_backend.metrics.models import (
    AirTemperature,
    Precipitation,
    WaterDischarge,
    WaterLevel,
    WaterTemperature,
    WaterVelocity,
)
from sapphire_backend.metrics.schema import AggregationFunctionParams, MetricParams

METRIC_MODEL_MAPPING = {
    MetricParams.water_discharge: WaterDischarge,
    MetricParams.water_level: WaterLevel,
    MetricParams.water_temperature: WaterTemperature,
    MetricParams.water_velocity: WaterVelocity,
    MetricParams.air_temperature: AirTemperature,
    MetricParams.precipitation: Precipitation,
}

AGGREGATION_MAPPING = {
    AggregationFunctionParams.average: Avg("average_value"),
    AggregationFunctionParams.minimum: Min("average_value"),
    AggregationFunctionParams.maximum: Max("average_value"),
}
