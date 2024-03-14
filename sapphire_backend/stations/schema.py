from datetime import datetime

from ninja import Field, FilterSchema, ModelSchema, Schema

from sapphire_backend.organizations.schema import BasinOutputSchema, RegionOutputSchema
from sapphire_backend.utils.mixins.schemas import UUIDSchemaMixin

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
    country: str
    latitude: float | None = None
    longitude: float | None = None
    timezone: str | None = None
    elevation: float | None = None


class SiteInputSchema(SiteBaseSchema, SiteBasinRegionInputSchema):
    pass


class SiteUpdateSchema(SiteInputSchema):
    country: str | None = None
    region_id: str | None = None
    basin_id: str | None = None


class SiteOutputSchema(SiteBaseSchema, SiteBasinRegionOutputSchema, UUIDSchemaMixin):
    id: int
    organization_uuid: str
    timezone: str | None = Field(None, alias="get_timezone_display")

    @staticmethod
    def resolve_organization_uuid(obj):
        return str(obj.organization.uuid)


class HydroStationBaseSchema(Schema):
    name: str
    description: str | None = None
    station_type: HydrologicalStation.StationType
    station_code: str
    measurement_time_step: int | None = None
    discharge_level_alarm: float | None = None
    historical_discharge_minimum: float | None = None
    historical_discharge_maximum: float | None = None
    bulletin_order: int | None = 0


class HydroStationInputSchema(HydroStationBaseSchema, Schema):
    site_uuid: str = None
    site_data: SiteInputSchema = None


class HydroStationUpdateSchema(HydroStationBaseSchema):
    name: str | None = None
    station_type: HydrologicalStation.StationType | None = None
    station_code: str | None = None
    site_data: SiteUpdateSchema | None = None


class HydroStationOutputDetailSchema(HydroStationBaseSchema, UUIDSchemaMixin):
    site: SiteOutputSchema
    id: int
    remarks: list[RemarkOutputSchema] = None


class HydrologicalStationFilterSchema(FilterSchema):
    site__uuid: str | None = None
    station_type: HydrologicalStation.StationType | None = None
    station_code: str | None = None


class HydrologicalStationStatsSchema(Schema):
    total: int
    manual: int
    auto: int


class MeteoStationBaseSchema(Schema):
    name: str
    description: str | None = None
    station_code: str


class MeteoStationInputSchema(SiteInputSchema, MeteoStationBaseSchema):
    site_uuid: str | None = None
    site_data: SiteInputSchema = None


class MeteoStationUpdateSchema(MeteoStationBaseSchema):
    name: str | None = None
    station_code: str | None = None
    site_data: SiteUpdateSchema | None = None


class MeteoStationOutputDetailSchema(MeteoStationBaseSchema, UUIDSchemaMixin):
    site: SiteOutputSchema
    id: int
    remarks: list[RemarkOutputSchema] = None


class MeteoStationStatsSchema(Schema):
    total: int


class VirtualStationBaseSchema(SiteBaseSchema, Schema):
    name: str
    description: str = ""
    station_code: str


class VirtualStationInputSchema(VirtualStationBaseSchema, SiteBasinRegionInputSchema):
    pass


class VirtualStationUpdateSchema(VirtualStationInputSchema):
    name: str | None = None
    station_code: str | None = None
    description: str | None = None
    region_id: str | None = None
    basin_id: str | None = None
    country: str | None = None


class VirtualStationListOutputSchema(VirtualStationBaseSchema, SiteBasinRegionOutputSchema, UUIDSchemaMixin):
    id: int
    timezone: str | None = Field(None, alias="get_timezone_display")
    station_type: str = "V"


class VirtualStationAssociationInputSchema(Schema):
    uuid: str
    weight: float


class VirtualStationAssociationSchema(Schema):
    name: str = Field(None, alias="hydro_station.name")
    weight: float
    id: int = Field(None, alias="hydro_station.id")
    uuid: str
    station_code: str = Field(None, alias="hydro_station.station_code")

    @staticmethod
    def resolve_uuid(obj):
        return str(obj.hydro_station.uuid)


class VirtualStationDetailOutputSchema(VirtualStationListOutputSchema):
    associations: list[VirtualStationAssociationSchema] = Field(None, alias="virtualstationassociation_set")
