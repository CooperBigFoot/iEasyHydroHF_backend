import logging

logger = logging.getLogger("discharge_norm_logger")


class DischargeNormParserException(Exception):
    """
    Base exception for all telegram parsing errors.
    """

    pass


class InvalidFileExtensionException(DischargeNormParserException):
    """
    Raised when an invalid token is encountered during parsing.
    """

    def __init__(self, file_extension: str, message: str = "Invalid file extension"):
        self.file_extension = file_extension
        logger.error(f"{message}: {file_extension}")
        super().__init__(f"{message}: {file_extension}")


class FileTooBigException(DischargeNormParserException):
    """
    Raised when an invalid token is encountered during parsing.
    """

    def __init__(
        self,
        file_size: float,
        max_size: float,
        message: str = "Maximum file size is {} MB, but uploaded file has {} MB",
    ):
        self.file_size = file_size
        self.max_size = max_size
        logger.error(message.format(max_size, file_size))
        super().__init__(message.format(max_size, file_size))


class MissingSheetsException(DischargeNormParserException):
    def __init__(
        self, required: list[str], found: list[str], message: str = "Missing required sheets: '{}', found: '{}'"
    ):
        self.required = required
        self.found = found
        msg = message.format(", ".join(required), ", ".join(found))
        logger.error(msg)
        super().__init__(msg)


class InvalidFileStructureException(DischargeNormParserException):
    def __init__(
        self, message: str = "Could not read the file, please check to template file to see the expected format"
    ):
        logger.error(f"{message}")
        super().__init__(f"{message}")


class SDKDataError(Exception):
    """
    Raised when an error occurs while getting SDK data.
    """

    def __init__(self, message: str):
        self.message = message
        logger.error(f"{message}")
        super().__init__(f"{message}")
