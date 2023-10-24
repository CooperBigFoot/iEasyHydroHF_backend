from ninja import Field, ModelSchema, Schema

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
    organization_uuid: str
    organization_id: int
    timezone: str = Field(None, alias="get_timezone_display")

    @staticmethod
    def resolve_organization_uuid(obj):
        return str(obj.organization.uuid)


class StationFilterSchema(Schema):
    station_type: Station.StationType = None
