import logging

logger = logging.getLogger("telegram_logger")


class TelegramParserException(Exception):
    """
    Base exception for all telegram parsing errors.
    """

    pass


class InvalidTokenException(TelegramParserException):
    """
    Raised when an invalid token is encountered during parsing.
    """

    def __init__(self, token: str | int, message: str = "Invalid token encountered"):
        self.token = token
        logger.error(f"{message}: {token}")
        super().__init__(f"{message}: {token}")


class UnsupportedSectionException(TelegramParserException):
    """
    Raised when an unsupported section code is encountered.
    """

    def __init(self, section_code: str, message: str = "Unsupported section code"):
        self.section_code = section_code
        logger.error(f"{message}: {section_code}")
        super().__init__(f"{message}: {section_code}")


class MissingSectionException(TelegramParserException):
    """
    Raised when a required section is missing from the telegram.
    """

    def __init__(self, section_name: str, message: str = "Missing required section"):
        self.section_name = section_name
        logger.error(f"{message}: {section_name}")
        super().__init__(f"{message}: {section_name}")


class TelegramAlreadyParsedException(TelegramParserException):
    """
    Raised when a telegram is a successfully parsed telegram already exists.
    """

    def __init__(self, telegram: str, message: str = "Telegram already ingested"):
        logger.error(f"{message}: {telegram}")
        super().__init__(f"{message}: {telegram}")
