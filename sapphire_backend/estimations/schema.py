from datetime import datetime
from typing import Literal

from ninja import FilterSchema, Schema


class DischargeModelBaseSchema(Schema):
    name: str
    param_a: float
    param_b: float
    param_c: float
    valid_from_local: datetime
    station_id: int
    uuid: str

    @staticmethod
    def resolve_uuid(obj):
        return str(obj.uuid)

    @staticmethod
    def resolve_valid_from_local(obj):
        transform_valid_from_local = obj.valid_from_local.date()
        return transform_valid_from_local


class DischargeModelCreateBaseSchema(Schema):
    name: str
    valid_from_local: str


class DischargeModelDeleteOutputSchema(Schema):
    name: str


class DischargeModelPointsPair(Schema):
    h: float
    q: float


class DischargeModelCreateInputPointsSchema(DischargeModelCreateBaseSchema):
    points: list[DischargeModelPointsPair]


class DischargeModelCreateInputDeltaSchema(DischargeModelCreateBaseSchema):
    param_delta: float
    from_model_uuid: str


class OrderQueryParamSchema(Schema):
    order_direction: Literal["ASC", "DESC"] = "DESC"
    order_param: Literal["timestamp_local", "avg_value"] = "timestamp_local"


class EstimationsViewSchema(Schema):
    view: Literal[
        "estimations_water_level_daily_average",
        "estimations_water_discharge_daily",
        "estimations_water_discharge_daily_average",
        "estimations_water_discharge_fiveday_average",
        "estimations_water_discharge_decade_average",
    ]


class EstimationsFilterSchema(FilterSchema):
    timestamp_local: datetime = None
    timestamp_local__gt: datetime = None
    timestamp_local__gte: datetime = None
    timestamp_local__lt: datetime = None
    timestamp_local__lte: datetime = None
    station_id: int = None
    station_id__in: list[int] = None
    avg_value__gt: float = None
    avg_value__gte: float = None
    avg_value__lt: float = None
    avg_value__lte: float = None


class EstimationsWaterDischargeDailyAverageOutputSchema(Schema):
    timestamp_local: datetime
    avg_value: float
