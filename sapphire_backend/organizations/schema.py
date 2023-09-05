from ninja import Field, ModelSchema, Schema

from sapphire_backend.utils.mixins.schemas import UUIDSchemaMixin

from .models import Organization


class OrganizationInputSchema(ModelSchema):
    class Config:
        model = Organization
        model_exclude = ["id", "uuid"]


class OrganizationUpdateSchema(ModelSchema):
    class Config:
        model = Organization
        model_exclude = ["id", "uuid"]
        model_fields_optional = "__all__"


class OrganizationOutputDetailSchema(UUIDSchemaMixin, OrganizationInputSchema):
    id: int
    timezone: str = Field(None, alias="get_timezone_display")


class OrganizationOutputListSchema(UUIDSchemaMixin, Schema):
    id: int
    name: str
