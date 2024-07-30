from datetime import datetime

from django.conf import settings
from ninja import Field, FilterSchema, Schema

from sapphire_backend.users.schema import UserOutputListSchema
from sapphire_backend.utils.mixins.schemas import UUIDSchemaMixin

from .choices import BulletinType


class BulletinTypeFilterSchema(FilterSchema):
    type: BulletinType = None


class BulletinBaseSchema(Schema):
    name: str
    type: BulletinType
    is_default: bool | None = False


class BulletinInputSchema(BulletinBaseSchema):
    pass


class BulletinUpdateSchema(BulletinBaseSchema):
    name: str | None = None
    type: BulletinType | None = None


class BulletinOutputSchema(UUIDSchemaMixin, BulletinBaseSchema):
    id: int
    filename: str
    user: UserOutputListSchema | None
    last_modified: datetime
    created_date: datetime
    size: float = Field(..., alias="filename.size")

    @staticmethod
    def resolve_filename(obj):
        if obj.filename.url.startswith("http"):
            return obj.filename.url
        else:
            return f"{settings.BACKEND_URL}{obj.filename.url}"


class BulletinTemplateTagSchema(Schema):
    name: str
    description: str


class BulletinTemplateTagOutputSchema(Schema):
    general: list[BulletinTemplateTagSchema]
    header: list[BulletinTemplateTagSchema]
    data: list[BulletinTemplateTagSchema]


class BulletinGenerateSchema(Schema):
    date: datetime
    stations: list[str]
    bulletins: list[str]
