from ninja import FilterSchema, Schema

from sapphire_backend.utils.mixins.schemas import UUIDSchemaMixin

from .choices import BulletinType


class BulletinTypeFilterSchema(FilterSchema):
    type: BulletinType


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
