from datetime import datetime
from typing import Literal

from ninja import FilterSchema, Schema

from sapphire_backend.utils.datetime_helper import SmartDatetime


class DischargeModelBaseSchema(Schema):
    name: str
    param_a: float
    param_b: float
    param_c: float
    valid_from: datetime
    station_id: int
    uuid: str

    @staticmethod
    def resolve_uuid(obj):
        return str(obj.uuid)

    @staticmethod
    def resolve_valid_from(obj):
        transform_valid_from = SmartDatetime(obj.valid_from, station=obj.station, local=False).local.date()
        return transform_valid_from


class DischargeModelCreateBaseSchema(Schema):
    name: str
    valid_from: str


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
    order_param: Literal["timestamp", "avg_value"] = "timestamp"


class EstimationsViewSchema(Schema):
    view: Literal[
        "estimations_water_level_daily_average",
        "estimations_water_discharge_daily",
        "estimations_water_discharge_daily_average",
        "estimations_water_discharge_fiveday_average",
        "estimations_water_discharge_decade_average",
    ]


class EstimationsFilterSchema(FilterSchema):
    timestamp: datetime = None
    timestamp__gt: datetime = None
    timestamp__gte: datetime = None
    timestamp__lt: datetime = None
    timestamp__lte: datetime = None
    station_id: int = None
    station_id__in: list[int] = None
    avg_value__gt: float = None
    avg_value__gte: float = None
    avg_value__lt: float = None
    avg_value__lte: float = None
