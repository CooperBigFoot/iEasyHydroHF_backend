from ninja import Schema


class Message(Schema):
    detail: str
    code: str = ""


class FieldMessage(Schema):
    field: str
    message: str


class UUIDSchemaMixin(Schema):
    uuid: str

    @staticmethod
    def resolve_uuid(obj):
        return str(obj.uuid)
