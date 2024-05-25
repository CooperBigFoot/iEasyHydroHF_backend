from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Literal

from ninja import Field, FilterSchema, ModelSchema, Schema

from sapphire_backend.utils.daily_precipitation_mapper import DailyPrecipitationCodeMapper
from sapphire_backend.utils.ice_phenomena_mapper import IcePhenomenaCodeMapper

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


class OperationalJournalIcePhenomenaSchema(Schema):
    intensity: int = Field(..., alias="avg_value")
    code: int = Field(None, alias="value_code")
    description: str | None = None

    @staticmethod
    def resolve_description(obj):
        return IcePhenomenaCodeMapper(obj["value_code"]).get_description() if obj else None


class OperationalJournalDailyPrecipitationSchema(Schema):
    value: int = Field(None, alias="avg_value")
    duration: int = Field(None, alias="value_code")
    description: str | None = None

    @staticmethod
    def resolve_description(obj):
        return DailyPrecipitationCodeMapper(obj["value_code"]).get_description() if obj else None


class OperationalJournalDailyDataSchema(Schema):
    IPO: list[OperationalJournalIcePhenomenaSchema]
    WTO: Decimal | None = None
    ATO: Decimal | None = None
    PD: OperationalJournalDailyPrecipitationSchema | None = None
    WLDA: Decimal | None = None
    WDDA: Decimal | None = None

    @staticmethod
    def resolve_WTO(obj):
        return round(obj["WTO"], 1) if obj["WTO"] else None


class OperationalJournalMorningEveningDataSchema(Schema):
    WLD: Decimal | None = None
    WDD: Decimal | None = None


class OperationalJournalMorningDataSchema(OperationalJournalMorningEveningDataSchema):
    water_level_trend: int | None = None


class OperationalJournalEveningDataSchema(OperationalJournalMorningEveningDataSchema):
    pass


class OperationalJournalDaySchema(Schema):
    morning_data: OperationalJournalMorningDataSchema
    evening_data: OperationalJournalEveningDataSchema
    daily_data: OperationalJournalDailyDataSchema


class OperationalJournalDischargeDataSchema(Schema):
    WLDC: Decimal
    WDD: Decimal
    RCSA: Decimal | None = None


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
