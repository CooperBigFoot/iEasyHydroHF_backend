from datetime import datetime

from ninja import Field, ModelSchema, Schema

from .models import Remark, Station


class RemarkInputSchema(ModelSchema):
    class Config:
        model = Remark
        model_fields = ["comment"]


class RemarkOutputSchema(RemarkInputSchema):
    last_modified: datetime
    created_date: datetime
    user: str = Field(None, alias="user.username")
    uuid: str

    @staticmethod
    def resolve_uuid(obj):
        return str(obj.uuid)


class StationInputSchema(Schema):
    name: str
    description: str = None
    station_type: str
    station_code: str
    country: str
    timezone: str = None
    basin_id: str = None
    latitude: float
    longitude: float
    region_id: str = None
    elevation: float = None
    is_automatic: bool
    is_virtual: bool
    measurement_time_step: int = None
    discharge_level_alarm: float = None


class StationUpdateSchema(ModelSchema):
    class Config:
        model = Station
        model_exclude = ["id", "slug", "organization"]
        model_fields_optional = "__all__"


class StationOutputDetailSchema(Schema):
    id: int
    uuid: str
    slug: str
    organization_uuid: str
    organization_id: int
    name: str
    description: str = None
    station_type: str
    station_code: str
    country: str
    latitude: float
    longitude: float
    elevation: float = None
    is_automatic: bool
    is_virtual: bool
    measurement_time_step: int = None
    discharge_level_alarm: float = None
    timezone: str = Field(None, alias="get_timezone_display")
    basin: str = Field(None, alias="basin.name")
    region: str = Field(None, alias="region.name")
    remarks: list[RemarkOutputSchema] = None

    @staticmethod
    def resolve_organization_uuid(obj):
        return str(obj.organization.uuid)

    @staticmethod
    def resolve_uuid(obj):
        return str(obj.uuid)


class StationFilterSchema(Schema):
    station_type: Station.StationType = None
