from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.utils.mixins.schemas import Message
from sapphire_backend.utils.permissions import OrganizationExists

from .exceptions import TelegramParserException
from .parser import KN15TelegramParser
from .schema import TelegramBulkInputSchema, TelegramInputSchema, TelegramOutputSchema


@api_controller("{organization_uuid}/telegrams", tags=["Telegrams"], auth=JWTAuth(), permissions=[OrganizationExists])
class TelegramsAPIController:
    @route.post("parse", response={201: TelegramOutputSchema, 400: Message})
    def parse_telegram(self, request, organization_uuid: str, encoded_telegram: TelegramInputSchema):
        parser = KN15TelegramParser(encoded_telegram.telegram)
        try:
            decoded = parser.parse()
            return 201, decoded
        except TelegramParserException as e:
            return 400, {"detail": str(e), "code": "invalid_telegram"}

    @route.post("parse-bulk", response={201: list[TelegramOutputSchema], 400: Message})
    def bulk_parse_telegram(self, request, organization_uuid: str, encoded_telegrams: TelegramBulkInputSchema):
        try:
            decoded_values = KN15TelegramParser.parse_bulk(telegrams=encoded_telegrams.telegrams, store_in_db=True)
            return 201, decoded_values
        except TelegramParserException as e:
            return 400, {"detail": str(e), "code": "invalid_telegram"}
