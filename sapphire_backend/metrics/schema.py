from datetime import datetime
from typing import Literal

from ninja import FilterSchema, Schema

from .choices import (
    HydrologicalMeasurementType,
    HydrologicalMetricName,
    MeteorologicalMeasurementType,
    MeteorologicalMetricName,
)


class BaseTimeseriesFilterSchema(FilterSchema):
    timestamp: datetime = None
    timestamp__gt: datetime = None
    timestamp__gte: datetime = None
    timestamp__lt: datetime = None
    timestamp__lte: datetime = None
    station_id: int = None
    station_id__in: list[int] = None
    station__station_code: str = None
    station__station_code__in: list[str] = None


class HydroMetricFilterSchema(BaseTimeseriesFilterSchema):
    avg_value__gt: float = None
    avg_value__gte: float = None
    avg_value__lt: float = None
    avg_value__lte: float = None
    metric_name: HydrologicalMetricName = None
    value_type: HydrologicalMeasurementType = None
    sensor_identifier: str = None


class MeteoMetricFilterSchema(BaseTimeseriesFilterSchema):
    value__gt: float = None
    value__gte: float = None
    value__lt: float = None
    value__lte: float = None
    metric_name: MeteorologicalMetricName = None
    value_type: MeteorologicalMeasurementType = None


class OrderQueryParamSchema(Schema):
    order_direction: Literal["asc", "desc"] = "desc"
    order_param: Literal["timestamp", "avg_value"] = "timestamp"


class HydrologicalMetricOutputSchema(Schema):
    avg_value: float
    timestamp: datetime
    metric_name: str
    value_type: str
    sensor_identifier: str
    station_id: int
