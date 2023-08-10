from ninja import Schema


class Message(Schema):
    detail: str
    code: str = ""


class UUIDSchemaMixin(Schema):
    uuid: str

    @staticmethod
    def resolve_uuid(obj):
        return str(obj.uuid)
