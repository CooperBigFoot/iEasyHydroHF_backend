from ninja import Field, ModelSchema, Schema

from sapphire_backend.utils.mixins.schemas import UUIDSchemaMixin

from .models import Basin, Organization, Region


class OrganizationInputSchema(ModelSchema):
    class Meta:
        model = Organization
        exclude = ["id", "uuid"]


class OrganizationUpdateSchema(ModelSchema):
    class Meta:
        model = Organization
        exclude = ["id", "uuid"]
        optional_fields = "__all__"


class OrganizationOutputDetailSchema(UUIDSchemaMixin, OrganizationInputSchema):
    id: int
    timezone: str | None = Field(None, alias="get_timezone_display")


class OrganizationOutputListSchema(UUIDSchemaMixin, Schema):
    id: int
    name: str
    secondary_name: str


class BasinInputSchema(ModelSchema):
    class Meta:
        model = Basin
        fields = ["name", "secondary_name"]


class BasinOutputSchema(BasinInputSchema):
    id: int
    uuid: str

    @staticmethod
    def resolve_uuid(obj):
        return str(obj.uuid)


class RegionInputSchema(ModelSchema):
    class Meta:
        model = Region
        fields = ["name", "secondary_name"]


class RegionOutputSchema(RegionInputSchema):
    id: int
    uuid: str

    @staticmethod
    def resolve_uuid(obj):
        return str(obj.uuid)
