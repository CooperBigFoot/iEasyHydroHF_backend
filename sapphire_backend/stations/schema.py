from ninja import ModelSchema, Schema

from .models import Station


class StationInputSchema(ModelSchema):
    class Config:
        model = Station
        model_exclude = ["id", "slug", "is_deleted", "organization"]


class StationUpdateSchema(ModelSchema):
    class Config:
        model = Station
        model_exclude = ["id", "slug", "organization"]
        model_fields_optional = "__all__"


class StationOutputDetailSchema(StationInputSchema):
    id: int
    slug: str
    organization_id: int


class StationOutputListSchema(Schema):
    station_code: str
    name: str
    basin: str
    region: str
    is_automatic: bool
