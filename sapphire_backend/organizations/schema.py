from ninja import ModelSchema, Schema

from .models import Organization


class OrganizationInputSchema(ModelSchema):
    class Config:
        model = Organization
        model_exclude = ["id", "is_active"]


class OrganizationUpdateSchema(ModelSchema):
    class Config:
        model = Organization
        model_exclude = ["id"]
        model_fields_optional = "__all__"


class OrganizationOutputDetailSchema(OrganizationInputSchema):
    id: int
    is_active: bool
    year_type: str
    language: str

    @staticmethod
    def resolve_timezone(obj):
        return obj.get_timezone_display()

    @staticmethod
    def resolve_year_type(obj):
        return obj.get_year_type_display()

    @staticmethod
    def resolve_language(obj):
        return obj.get_language_display()


class OrganizationOutputListSchema(Schema):
    id: int
    name: str
