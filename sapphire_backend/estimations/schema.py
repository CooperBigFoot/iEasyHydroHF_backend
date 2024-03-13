from datetime import datetime

from ninja import Schema


class DischargeModelBaseSchema(Schema):
    name: str
    param_a: float
    param_b: float
    param_c: float
    valid_from: datetime
    station_id: int


class DischargeModelOutputDetailSchema(DischargeModelBaseSchema):
    id: int
    uuid: str

    @staticmethod
    def resolve_uuid(obj):
        return str(obj.uuid)


class DischargeModelCreateBaseSchema(Schema):
    name: str
    valid_from: str


class DischargeModelPointsPair(Schema):
    h: float
    q: float


class DischargeModelCreateInputPointsSchema(DischargeModelCreateBaseSchema):
    points: list[DischargeModelPointsPair]


class DischargeModelCreateInputDeltaSchema(DischargeModelCreateBaseSchema):
    param_delta: float
    from_model_id: int
