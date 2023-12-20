from datetime import datetime

from ninja import Field, ModelSchema, Schema

from sapphire_backend.organizations.schema import BasinOutputSchema, RegionOutputSchema

from .models import HydrologicalStation, Remark


class RemarkInputSchema(ModelSchema):
    class Meta:
        model = Remark
        fields = ["comment"]


class RemarkOutputSchema(RemarkInputSchema):
    last_modified: datetime
    created_date: datetime
    user: str = Field(None, alias="user.username")
    uuid: str

    @staticmethod
    def resolve_uuid(obj):
        return str(obj.uuid)


class SiteBasinRegionInputSchema(Schema):
    region_id: str
    basin_id: str


class SiteBasinRegionOutputSchema(Schema):
    basin: BasinOutputSchema
    region: RegionOutputSchema


class SiteBaseSchema(Schema):
    name: str
    country: str
    latitude: float
    longitude: float
    timezone: str = None
    elevation: float = None


class SiteInputSchema(SiteBaseSchema, SiteBasinRegionInputSchema):
    pass


class SiteUpdateSchema(SiteInputSchema):
    name: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    region_id: str | None = None
    basin_id: str | None = None


class SiteOutputSchema(SiteBaseSchema, SiteBasinRegionOutputSchema):
    id: int
    uuid: str
    organization_uuid: str
    timezone: str = Field(None, alias="get_timezone_display")

    @staticmethod
    def resolve_organization_uuid(obj):
        return str(obj.organization.uuid)

    @staticmethod
    def resolve_uuid(obj):
        return str(obj.uuid)


class HydroStationBaseSchema(Schema):
    name: str | None = None
    description: str | None = None
    station_type: HydrologicalStation.StationType
    station_code: str
    measurement_time_step: int | None = None
    discharge_level_alarm: float | None = None
    historical_discharge_minimum: float | None = None
    historical_discharge_maximum: float | None = None
    decadal_discharge_norm: float | None = None
    monthly_discharge_norm: dict[int, float] | None = None


class HydroStationInputSchema(HydroStationBaseSchema, Schema):
    site_uuid: str = None
    site_data: SiteInputSchema = None


class HydroStationUpdateSchema(HydroStationBaseSchema):
    station_type: HydrologicalStation.StationType | None = None
    station_code: str | None = None
    site_data: SiteUpdateSchema | None = None


class HydroStationOutputDetailSchema(HydroStationBaseSchema):
    site: SiteOutputSchema
    id: int
    uuid: str
    remarks: list[RemarkOutputSchema] = None

    @staticmethod
    def resolve_uuid(obj):
        return str(obj.uuid)
