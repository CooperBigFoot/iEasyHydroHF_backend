class TelegramParserException(Exception):
    """
    Base exception for all telegram parsing errors.
    """

    pass


class InvalidTokenException(TelegramParserException):
    """
    Raised when an invalid token is encountered during parsing.
    """

    def __init__(self, token: str, message: str = "Invalid token encountered"):
        self.token = token
        super().__init__(f"{message}: {token}")


class UnsupportedSectionException(TelegramParserException):
    """
    Raised when an unsupported section code is encountered.
    """

    def __init(self, section_code: str, message: str = "Unsupported section code"):
        self.section_code = section_code
        super().__init__(f"{message}: {section_code}")


class MissingSectionError(TelegramParserException):
    """
    Raised when a required section is missing from the telegram.
    """

    def __init__(self, section_name: str, message: str = "Missing required section"):
        self.section_name = section_name
        super().__init__(f"{message}: {section_name}")
