from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from ninja import Field, FilterSchema, ModelSchema, Schema
from ninja.errors import ValidationError
from pydantic import field_validator

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
    station_code: str = Field(..., alias="station__station_code")
    station_uuid: str
    value_code: int | None = None

    @staticmethod
    def resolve_station_uuid(obj):
        return str(obj.get("station__uuid"))


class TimestampGroupedHydroMetricSchema(Schema):
    timestamp_local: datetime
    WLD: float | None = None
    WLDA: float | None = None
    ATO: float | None = None
    ATDA: float | None = None
    WTDA: float | None = None
    WTO: float | None = None
    PD: float | None = None


class HFChartSchema(Schema):
    x: datetime = Field(..., alias="timestamp_local")
    y: float

    @staticmethod
    def resolve_y(obj):
        return obj.get("WLD") or obj.get("WLDA") or obj.get("WDDA")


class MeasuredDischargeMeasurementSchema(Schema):
    date: str
    h: float
    q: float
    f: float | None


class MetricValueWithMetadata(Schema):
    value: int | float | str
    timestamp_local: datetime | None = None
    sensor_identifier: str | None = None
    value_type: str | None = None
    has_history: bool | None = None
    allow_manual_override: bool | None = False


class IcePhenomenaWithMetadata(Schema):
    ice_phenomena_values: list[float] | None = None
    ice_phenomena_codes: list[int] | None = None
    sensor_identifiers: list[str] | None = None
    timestamps_local: list[datetime] | None = None
    has_history: list[bool] | None = None


class PrecipitationWithMetadata(Schema):
    daily_precipitation_value: float | None = None
    daily_precipitation_code: int | None = None
    sensor_identifier: str | None = None
    timestamp_local: datetime | None = None
    has_history: bool | None = None


class OperationalJournalDailyVirtualDataSchema(Schema):
    id: str
    date: str
    station_id: int
    water_discharge_morning: MetricValueWithMetadata
    water_discharge_evening: MetricValueWithMetadata
    water_discharge_average: MetricValueWithMetadata


class OperationalJournalDailyDataSchema(OperationalJournalDailyVirtualDataSchema):
    trend: int | str | None = "--"

    # Values with metadata
    water_level_morning: MetricValueWithMetadata
    water_level_evening: MetricValueWithMetadata
    water_level_average: MetricValueWithMetadata
    water_temperature: MetricValueWithMetadata
    air_temperature: MetricValueWithMetadata

    ice_phenomena: IcePhenomenaWithMetadata
    daily_precipitation: PrecipitationWithMetadata


class OperationalJournalDischargeDataSchema(Schema):
    id: str
    date: str
    station_id: int
    water_level: MetricValueWithMetadata
    water_discharge: MetricValueWithMetadata
    cross_section: MetricValueWithMetadata


class OperationalJournalDecadalBaseSchema(Schema):
    id: str
    decade: int | str


class OperationalJournalDecadalHydroVirtualDataSchema(OperationalJournalDecadalBaseSchema):
    water_discharge: MetricValueWithMetadata


class OperationalJournalDecadalHydroDataSchema(OperationalJournalDecadalHydroVirtualDataSchema):
    water_level: MetricValueWithMetadata


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
    station_code: str = Field(..., alias="station__station_code")
    station_uuid: str

    @staticmethod
    def resolve_station_uuid(obj):
        return str(obj.get("station__uuid"))


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
        if obj.norm_type == NormType.PENTADAL:
            return PentadDecadeHelper.calculate_pentad_date(obj.ordinal_number)
        elif obj.norm_type == NormType.MONTHLY:
            return datetime(datetime.utcnow().year, obj.ordinal_number, 1, 12, tzinfo=timezone.utc)
        else:
            return PentadDecadeHelper.calculate_decade_date(obj.ordinal_number)

    @staticmethod
    def resolve_value(obj):
        if obj.value is None:
            return None

        number = obj.value
        if number == 0:
            return "0.000"
        elif number < 1:
            # For values < 1, show 3 decimal places
            return format(number, ".3f")
        elif number < 10:
            # For values >= 1 and < 10, show 2 decimal places
            return format(number, ".2f")
        elif number < 100:
            # For values >= 10 and < 100, show 1 decimal place
            return format(number, ".1f")
        else:
            # For values >= 100, show no decimal places
            return str(int(number))


class MeteorologicalNormOutputSchema(HydrologicalNormOutputSchema):
    class Meta(HydrologicalNormOutputSchema.Meta):
        model = MeteorologicalNorm
        fields = ["ordinal_number", "value", "norm_metric"]


class BulkDataDownloadInputSchema(Schema):
    hydro_station_manual_uuids: list[str] = None
    hydro_station_auto_uuids: list[str] = None
    meteo_station_uuids: list[str] = None
    virtual_station_uuids: list[str] = None


class ViewType(str, Enum):
    MEASUREMENTS = "measurements"  # Raw measurements from HydrologicalMetric
    DAILY = "daily"  # Daily averages from estimation models


class DisplayType(str, Enum):
    INDIVIDUAL = "individual"  # Each metric as separate records
    GROUPED = "grouped"  # Metrics grouped by timestamp


class MetricViewTypeSchema(Schema):
    view_type: ViewType


class MetricDisplayTypeSchema(Schema):
    display_type: DisplayType


class DetailedDailyHydroMetricSchema(Schema):
    date: datetime
    id: datetime
    daily_average_water_level: float | None
    morning_water_level: float | None
    morning_water_level_timestamp: datetime | None
    evening_water_level: float | None
    evening_water_level_timestamp: datetime | None
    manual_daily_average_water_level: float | None
    min_water_level: float | None
    min_water_level_timestamp: datetime | None
    max_water_level: float | None
    max_water_level_timestamp: datetime | None
    daily_average_air_temperature: float | None
    daily_average_water_temperature: float | None


class DetailedDailyHydroMetricFilterSchema(Schema):
    station: int
    metric_name__in: list[HydrologicalMetricName]
    timestamp_local__gte: datetime
    timestamp_local__lt: datetime

    @field_validator("metric_name__in")
    @classmethod
    def validate_wld_metric_present(cls, v):
        if not v or HydrologicalMetricName.WATER_LEVEL_DAILY not in v:
            raise ValidationError("WATER_LEVEL_DAILY (WLD) metric is required")
        return v

    @field_validator("timestamp_local__lt")
    @classmethod
    def validate_date_range(cls, v, info):
        if "timestamp_local__gte" in info.data:
            date_range = v - info.data["timestamp_local__gte"]
            if date_range.days > 365:
                raise ValidationError("Date range cannot be more than 365 days")
        return v


class UpdateHydrologicalMetricSchema(Schema):
    # Fields to identify the metric
    timestamp_local: datetime
    station_id: int
    metric_name: str
    value_type: str
    sensor_identifier: str = ""  # matches the blank=True in model

    # New value and metadata
    new_value: float
    comment: str = ""

    value_code: int | None = None


class UpdateHydrologicalMetricResponseSchema(Schema):
    success: bool
    message: str


class SDKDataValueSchema(Schema):
    value: float
    value_type: str
    timestamp_local: datetime
    timestamp_utc: datetime
    value_code: int | None = None


class SDKDataVariableSchema(Schema):
    variable_code: str
    unit: str
    values: list[SDKDataValueSchema]


class SDKOutputSchema(Schema):
    station_id: int
    station_uuid: str
    station_code: str
    station_name: str
    station_type: Literal["hydro", "meteo"]
    data: list[SDKDataVariableSchema]


class PaginatedSDKOutputSchema(Schema):
    count: int
    next: str | None = None
    previous: str | None = None
    results: list[SDKOutputSchema]


class SDKDataFiltersSchema(FilterSchema):
    timestamp_local: datetime = None
    timestamp_local__gt: datetime = None
    timestamp_local__gte: datetime = None
    timestamp_local__lt: datetime = None
    timestamp_local__lte: datetime = None
    timestamp: datetime = None
    timestamp__gt: datetime = None
    timestamp__gte: datetime = None
    timestamp__lt: datetime = None
    timestamp__lte: datetime = None
    station: int = None
    station__in: list[int] = None
    station__station_code: str = None
    station__station_code__in: list[str] = None
    metric_name__in: list[HydrologicalMetricName | MeteorologicalMetricName] = None
