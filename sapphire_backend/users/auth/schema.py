from ninja import Schema
from ninja_jwt.schema import TokenObtainPairInputSchema
from ninja_jwt.tokens import RefreshToken

from ..schema import UserOutputDetailSchema


class TokenObtainOutputSchema(Schema):
    access: str
    refresh: str
    user: UserOutputDetailSchema


class TokenObtainInputSchema(TokenObtainPairInputSchema):
    @classmethod
    def get_token(cls, user) -> dict:
        values = {}
        refresh = RefreshToken.for_user(user)
        values["refresh"] = str(refresh)
        values["access"] = str(refresh.access_token)
        values.update(user=UserOutputDetailSchema.from_orm(user))
        return values

    @classmethod
    def get_response_schema(cls) -> type[Schema]:
        return TokenObtainOutputSchema
