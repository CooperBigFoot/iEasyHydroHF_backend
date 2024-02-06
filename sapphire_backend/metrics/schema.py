from datetime import datetime
from enum import Enum

from ninja import FilterSchema, Schema

from .choices import (
    HydrologicalMeasurementType,
    HydrologicalMetricName,
    MeteorologicalMeasurementType,
    MeteorologicalMetricName,
)


class TimeseriesGeneralFilterSchema(FilterSchema):
    station_id: int = None
    timestamp: datetime = None
    timestamp: datetime = None


class HydrologicalMetricFilterSchema(TimeseriesGeneralFilterSchema):
    average_value: float = None
    value_type: HydrologicalMeasurementType = None
    metric_name: HydrologicalMetricName = None
    sensor_identifier: str = None


class MeteorologicalMetricFilterSchema(TimeseriesGeneralFilterSchema):
    value: float = None
    value_type: MeteorologicalMeasurementType = None
    metric_name: MeteorologicalMetricName = None


class OrderParams(str, Enum):
    timestamp = "timestamp"
    average_value = "average_value"


class OrderDirectionParams(str, Enum):
    ascending = "ASC"
    descending = "DESC"


class OrderQueryParams(Schema):
    order_param: OrderParams = OrderParams.timestamp
    order_direction: OrderDirectionParams = OrderDirectionParams.descending


class HydrologicalMetricOutputSchema(Schema):
    avg_value: float
    timestamp: datetime
    metric_name: str
    value_type: str
    sensor_identifier: str
