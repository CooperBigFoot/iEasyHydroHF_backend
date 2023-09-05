from ninja import Schema
from ninja_jwt.schema import TokenObtainPairInputSchema

from ..schema import UserOutputDetailSchema


class TokenObtainOutputSchema(Schema):
    access: str
    refresh: str
    user: UserOutputDetailSchema


class TokenObtainInputSchema(TokenObtainPairInputSchema):
    def to_response_schema(self) -> Schema:
        _schema_type = self.get_response_schema()
        out_dict = self.dict(exclude={"password", "username"})
        out_dict.update(user=UserOutputDetailSchema.from_orm(self._user))
        return _schema_type(**out_dict)

    @classmethod
    def get_response_schema(cls) -> type[Schema]:
        return TokenObtainOutputSchema
