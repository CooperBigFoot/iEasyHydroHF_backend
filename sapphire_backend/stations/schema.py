from datetime import datetime

from ninja import Field, ModelSchema, Schema

from .models import HydrologicalStation, Remark, Site


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


class SiteInputSchema(Schema):
    name: str
    country: str
    latitude: float
    longitude: float
    timezone: str = None
    elevation: float = None
    region: str
    basin: str


class SiteUpdateSchema(SiteInputSchema):
    class Meta:
        model = Site
        exclude = ["id", "uuid", "organization"]
        optional_fields = "__all__"


class SiteOutputSchema(SiteInputSchema):
    id: int
    uuid: str
    organization_uuid: str
    basin: str = Field(None, alias="basin.name")
    region: str = Field(None, alias="region.name")
    timezone: str = Field(None, alias="get_timezone_display")

    @staticmethod
    def resolve_organization_uuid(obj):
        return str(obj.organization.uuid)

    @staticmethod
    def resolve_uuid(obj):
        return str(obj.uuid)


class StationInputSchema(Schema):
    site_uuid: str = None
    site_data: SiteInputSchema = None
    name: str = None
    description: str = None
    station_type: HydrologicalStation.StationType
    station_code: str
    measurement_time_step: int | None = None
    discharge_level_alarm: float | None = None
    historical_discharge_minimum: float | None = None
    historical_discharge_maximum: float | None = None
    decadal_discharge_norm: float | None = None
    monthly_discharge_norm: dict[int, float] | None = None


class StationUpdateSchema(StationInputSchema):
    site: SiteUpdateSchema

    class Meta:
        optional_fields = "__all__"


class StationOutputDetailSchema(StationInputSchema):
    site: SiteOutputSchema
    id: int
    uuid: str
    remarks: list[RemarkOutputSchema] = None

    @staticmethod
    def resolve_uuid(obj):
        return str(obj.uuid)
