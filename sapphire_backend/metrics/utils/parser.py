from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd
from ninja import File

from sapphire_backend.metrics.exceptions import (
    FileTooBigException,
    InvalidFileExtensionException,
    InvalidFileStructureException,
    MissingSheetsException,
)


class BaseNormFileParser(ABC):
    def __init__(self, file: File):
        self.file = file
        self.max_file_size = 2 * 1024 * 1024
        self._validate_file_size()
        self._validate_file_extension()
        self.sheets = self._get_sheet_names()

    def _validate_file_extension(self):
        extension = Path(self.file.name).suffix
        if extension not in [".xlsx", ".xls", ".ods"]:
            raise InvalidFileExtensionException(extension)

    def _validate_file_size(self):
        if self.file.size > self.max_file_size:
            raise FileTooBigException(self.file.size / 1024 / 1024, self.max_file_size / 1024 / 1024)

    def _load_file(self):
        try:
            return pd.read_excel(self.file, sheet_name=self.sheets, nrows=2)
        except ValueError:
            raise MissingSheetsException(self.sheets, pd.ExcelFile(self.file).sheet_names)

    @abstractmethod
    def _get_sheet_names(self):
        pass

    @abstractmethod
    def parse(self):
        pass


class MonthlyDischargeNormFileParser(BaseNormFileParser):
    def _get_sheet_names(self):
        return ["discharge"]

    def parse(self):
        data = self._load_file()
        parsed_data = {}

        for sheet in data.keys():
            df = data[sheet]
            if len(df.columns) != 13:
                raise InvalidFileStructureException("Invalid number of columns, need to have 12 values.")
            parsed_data[sheet] = []
            for col in df.columns[1:]:
                parsed_data[sheet].append({"ordinal_number": int(col), "value": float(df[col].iloc[0])})

        return parsed_data


class DecadalDischargeNormFileParser(BaseNormFileParser):
    def _get_sheet_names(self):
        return ["discharge"]

    def parse(self):
        data = self._load_file()
        parsed_data = {}

        for sheet in data.keys():
            df = data[sheet]
            if len(df.columns) != 37:
                raise InvalidFileStructureException("Invalid number of columns, need to have 36 values.")
            parsed_data[sheet] = []
            for col in df.columns[1:]:
                if isinstance(col, int):
                    parsed_data[sheet].append({"ordinal_number": col, "value": float(df[col])})
                else:
                    # 1. Dec, 2. Dec
                    parsed_data[sheet].append(
                        {"ordinal_number": int(col.split(".")[0]), "value": float(df[col].iloc[0])}
                    )

        return parsed_data


class MonthlyMeteoNormFileParser(MonthlyDischargeNormFileParser):
    def _get_sheet_names(self):
        return ["precipitation", "temperature"]


class DecadalMeteoNormFileParser(DecadalDischargeNormFileParser):
    def _get_sheet_names(self):
        return ["precipitation", "temperature"]
