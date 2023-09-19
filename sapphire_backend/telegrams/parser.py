from abc import ABC, abstractmethod

from sapphire_backend.stations.models import Station
from sapphire_backend.telegrams.exceptions import (
    InvalidTokenException,
    MissingSectionError,
    UnsupportedSectionException,
)


class BaseTelegramParser(ABC):
    def __init__(self, telegram: str):
        self.telegram = telegram.strip()
        self.tokens = self.tokenize()

    def tokenize(self) -> list[str]:
        """
        Breaks the telegram into tokens for easier parsing.
        """
        return self.telegram.split()

    @abstractmethod
    def parse(self):
        """
        Main parsing method.
        Must be implemented by subclasses.
        """
        pass

    def validate_token(self, token: str) -> bool:
        """
        Validates the given token.
        Can be overriden by subclasses for special validation rules.
        Base class implementation returns True for every token.
        """
        return True

    def get_next_token(self) -> str:
        """
        Returns the next token from the list of tokens, if available.
        """
        if self.tokens:
            return self.tokens.pop(0)
        raise MissingSectionError("Unexpected end of telegram")

    @staticmethod
    def validate_station(station_code: str) -> None:
        if not station_code.isdigit() or len(station_code) != 5:
            raise InvalidTokenException(f"Invalid station code: {station_code}")
        if not Station.objects.filter(station_code=station_code).exists():
            raise InvalidTokenException(f"Station with code {station_code} does not exist")

    @classmethod
    def parse_bulk(cls, telegrams: list[str]) -> list:
        """
        Parses a list of telegrams and returns a list of parsed results.
        """
        return [cls(telegram).parse() for telegram in telegrams]


class KN15TelegramParser(BaseTelegramParser):
    def __init__(self, telegram: str):
        super().__init__(telegram)

    def parse(self):
        """
        Implements the parsing logic for KN15 telegrams.
        """

        # start by parsing section zero
        section_zero = self.parse_section_zero()

        if section_zero["section_code"] == 1:
            section_one = self.parse_section_one()

        elif section_zero["section_code"] == 2:
            section_one = self.parse_section_one()
            # section_three = self.parse_section_three()
            # section_six = self.parse_section_six()

        else:
            raise UnsupportedSectionException(section_zero["section_code"])

        return {"section_zero": section_zero, "section_one": section_one}

    def parse_section_zero(self):
        """
        Parses section 0 of the KN15 telegram.
        Section 0 contains the station code, date, and section code.
        """
        station_code = self.get_next_token()
        self.validate_station(station_code)

        # date_token = self.get_next_token()
        # day_in_month = int(date_token[:2])
        # hour = int(date_token[2:4])
        # section_code = int(date_token[4])

    def parse_section_one(self):
        """
        Parses section 1 of the KN15 telegram.
        """
        pass

    def parse_section_three(self):
        """
        Parses section 3 of the KN15 telegram.
        """
        pass

    def parse_section_six(self):
        """
        Parses section 6 of the KN15 telegram.
        """
        pass
