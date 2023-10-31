from datetime import datetime
from enum import Enum
from uuid import UUID

from django.db.models.expressions import Q
from ninja import FilterSchema, Schema


class TimeseriesFiltersSchema(FilterSchema):
    sensor_uuid: UUID | None
    timestamp__lte: datetime | None
    timestamp__gte: datetime | None
    average_value__lte: float | None
    average_value__gte: float | None

    def filter_sensor_uuid(self, value: bool) -> Q:
        return Q(sensor=value) if value else Q(sensor__is_default=True)


class OrderParams(str, Enum):
    timestamp = "timestamp"
    average_value = "average_value"


class OrderQueryParams(Schema):
    param: OrderParams = OrderParams.timestamp
    descending: bool = False


class MetricParams(str, Enum):
    water_discharge = "water_discharge"
    water_level = "water_level"
    water_velocity = "water_velocity"
    water_temperature = "water_temp"
    air_temperature = "air_temp"
    precipitation = "precipitation"


class AggregationFunctionParams(str, Enum):
    average = "avg"
    minimum = "min"
    maximum = "max"


class LatestMetricOutputSchema(Schema):
    timestamp: datetime


class TimeseriesOutputSchema(Schema):
    timestamp: datetime
    minimum_value: float | None
    average_value: float
    maximum_value: float | None
    unit: str


class TimeseriesGroupingOutputSchema(Schema):
    bucket: datetime
    value: float
    unit: str
