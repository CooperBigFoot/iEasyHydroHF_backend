from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from ninja import Field, FilterSchema, ModelSchema, Schema

from .choices import (
    HydrologicalMeasurementType,
    HydrologicalMetricName,
    MeteorologicalMeasurementType,
    MeteorologicalMetricName,
    MeteorologicalNormMetric,
    NormType,
)
from .models import HydrologicalNorm, MeteorologicalNorm
from .utils.helpers import PentadDecadeHelper


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
    metric_name__in: list[MeteorologicalMetricName] = None
    value_type__in: list[MeteorologicalMeasurementType] = None


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


class TimestampGroupedHydroMetricSchema(Schema):
    timestamp_local: datetime
    WLD: float | None = None
    ATO: float | None = None
    WTO: float | None = None
    PD: float | None = None


class HFChartSchema(Schema):
    x: datetime = Field(..., alias="timestamp_local")
    y: float = Field(..., alias="WLD")


class MeasuredDischargeMeasurementSchema(Schema):
    date: str
    h: float
    q: float
    f: float | None


class OperationalJournalDailyVirtualDataSchema(Schema):
    id: str
    date: str
    water_discharge_morning: float | str
    water_discharge_evening: float | str
    water_discharge_average: float | str


class OperationalJournalDailyDataSchema(OperationalJournalDailyVirtualDataSchema):
    water_level_morning: int | str
    trend: int | str | None = "--"
    water_level_evening: int | str
    water_level_average: int | str
    ice_phenomena: str | None = "--"
    daily_precipitation: str | None = "--"
    water_temperature: float | str
    air_temperature: float | str


class OperationalJournalDischargeDataSchema(Schema):
    id: str
    date: str
    water_level: int | str
    water_discharge: float | str
    cross_section: float | str


class OperationalJournalDecadalBaseSchema(Schema):
    id: str
    decade: int | str


class OperationalJournalDecadalHydroVirtualDataSchema(OperationalJournalDecadalBaseSchema):
    water_discharge: float | str


class OperationalJournalDecadalHydroDataSchema(OperationalJournalDecadalHydroVirtualDataSchema):
    water_level: int | str


class OperationalJournalDecadalMeteoDataSchema(OperationalJournalDecadalBaseSchema):
    precipitation: float | str
    temperature: float | str


class OperationalJournalDecadalDataStationType(Schema):
    station_type: Literal["hydro", "meteo"]


class MeteorologicalMetricOutputSchema(Schema):
    value: float
    timestamp_local: datetime
    metric_name: MeteorologicalMetricName
    station_id: int


class MeteorologicalManualInputSchema(Schema):
    month: int
    year: int
    decade: int
    precipitation: float
    temperature: float


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


class HydrologicalNormTypeFiltersSchema(FilterSchema):
    norm_type: NormType


class MeteorologicalNormTypeFiltersSchema(HydrologicalNormTypeFiltersSchema):
    norm_metric: MeteorologicalNormMetric


class HydrologicalNormOutputSchema(ModelSchema):
    timestamp_local: datetime

    class Meta:
        model = HydrologicalNorm
        fields = ["ordinal_number", "value"]

    @staticmethod
    def resolve_timestamp_local(obj):
        if obj.norm_type == NormType.MONTHLY:
            return datetime(datetime.utcnow().year, obj.ordinal_number, 1, 12, tzinfo=timezone.utc)
        else:
            return PentadDecadeHelper.calculate_decade_date(obj.ordinal_number)


class MeteorologicalNormOutputSchema(HydrologicalNormOutputSchema):
    class Meta(HydrologicalNormOutputSchema.Meta):
        model = MeteorologicalNorm


class BulkDataDownloadInputSchema(Schema):
    hydro_station_manual_uuids: list[str] = None
    hydro_station_auto_uuids: list[str] = None
    meteo_station_uuids: list[str] = None
    virtual_station_uuids: list[str] = None


class MetricViewTypeSchema(Schema):
    view_type: Literal["raw", "grouped", "daily"]


class MetricDisplayTypeSchema(Schema):
    display_type: Literal["grid", "chart"]


class MetricDailyAggregationTypeSchema(Schema):
    metric_type: Literal[
        "water_level_daily",
        "water_discharge_daily",
        "water_discharge_daily_virtual",
        "water_temperature_daily",
        "air_temperature_daily",
    ]
