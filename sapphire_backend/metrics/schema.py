from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from ninja import FilterSchema, ModelSchema, Schema

from .choices import (
    HydrologicalMeasurementType,
    HydrologicalMetricName,
    MeteorologicalMeasurementType,
    MeteorologicalMetricName,
    NormType,
)
from .models import DischargeNorm
from .utils.helpers import calculate_decade_date


class BaseTimeseriesFilterSchema(FilterSchema):
    timestamp_local: datetime = None
    timestamp_local__gt: datetime = None
    timestamp_local__gte: datetime = None
    timestamp_local__lt: datetime = None
    timestamp_local__lte: datetime = None
    station: int = None
    station__in: list[int] = None
    station__station_code: str = None
    station__station_code__in: list[str] = None


class HydroMetricFilterSchema(BaseTimeseriesFilterSchema):
    avg_value__gt: float = None
    avg_value__gte: float = None
    avg_value__lt: float = None
    avg_value__lte: float = None
    metric_name__in: list[HydrologicalMetricName] = None
    value_type__in: list[HydrologicalMeasurementType] = None
    sensor_identifier: str = None


class MeteoMetricFilterSchema(BaseTimeseriesFilterSchema):
    value__gt: float = None
    value__gte: float = None
    value__lt: float = None
    value__lte: float = None
    metric_name: MeteorologicalMetricName = None
    value_type: MeteorologicalMeasurementType = None


class OrderQueryParamSchema(Schema):
    order_direction: Literal["ASC", "DESC"] = "DESC"
    order_param: Literal["timestamp_local", "avg_value"] = "timestamp_local"


class HydrologicalMetricOutputSchema(Schema):
    avg_value: float
    timestamp_local: datetime
    metric_name: HydrologicalMetricName
    value_type: str
    sensor_identifier: str
    station_id: int
    value_code: int | None


class OperationalJournalDailyMeasurement(Schema):
    time: str
    WLD: float
    trend: int | None = None
    ATO: float | None = None
    WTO: float | None = None
    IPO: float | None = None
    WDD: float | None = None
    PD: float | None = None
    value_code: int | None = None


class OperationalJournalOutputSchema(Schema):
    date: str
    measurements: list[OperationalJournalDailyMeasurement]


class MeteorologicalMetricOutputSchema(Schema):
    value: float
    timestamp_local: datetime
    metric_name: MeteorologicalMetricName
    station_id: int


class MetricCountSchema(Schema):
    metric_name: HydrologicalMetricName | MeteorologicalMetricName | Literal["total"]
    metric_count: int


class MetricTotalCountSchema(Schema):
    total: int


class TimeBucketAggregationFunctions(str, Enum):
    count: str = "COUNT"
    min: str = "MIN"
    max: str = "MAX"
    avg: str = "AVG"
    sum: str = "SUM"


class TimeBucketQueryParams(Schema):
    interval: str
    agg_func: TimeBucketAggregationFunctions
    limit: int = 100


class DischargeNormTypeFiltersSchema(FilterSchema):
    norm_type: NormType


class DischargeNormOutputSchema(ModelSchema):
    timestamp_local: datetime

    class Meta:
        model = DischargeNorm
        fields = ["ordinal_number", "value"]

    @staticmethod
    def resolve_timestamp_local(obj):
        if obj.norm_type == NormType.MONTHLY:
            return datetime(datetime.utcnow().year, obj.ordinal_number, 1, 12, tzinfo=timezone.utc)
        else:
            return calculate_decade_date(obj.ordinal_number)
