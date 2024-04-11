from abc import ABC, abstractmethod
from pathlib import Path

from ninja import File

from sapphire_backend.metrics.exceptions import FileTooBigException, InvalidFileExtensionException


class BaseNormFileParser(ABC):
    def __init__(self, file: File):
        self.file = file
        self.max_file_size = 2 * 1024 * 1024
        self._validate_file_size()
        self._validate_file_extension()
        self._validate_file_structure()

    def _validate_file_extension(self):
        extension = Path(self.file.name).suffix
        if not extension == ".xlsx":
            raise InvalidFileExtensionException(extension)

    def _validate_file_size(self):
        if self.file.size > self.max_file_size:
            raise FileTooBigException(self.file.size / 1024 / 1024)

    @abstractmethod
    def _validate_file_structure(self):
        raise NotImplementedError("BaseNormFileParser subclass must implement this method.")

    @abstractmethod
    def parse(self):
        raise NotImplementedError("BaseNormFileParser subclass must implement this method.")


class MonthlyDischargeNormFileParser(BaseNormFileParser):
    def _validate_file_structure(self):
        pass

    def parse(self):
        pass


class DecadalDischargeNormFileParser(BaseNormFileParser):
    def _validate_file_structure(self):
        pass

    def parse(self):
        pass
