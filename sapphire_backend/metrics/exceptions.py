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

    def __init__(self, file_size: float, message: str = "Maximum file size is"):
        self.file_size = file_size
        logger.error(f"{message}: {file_size}")
        super().__init__(f"{message}: {file_size}")
