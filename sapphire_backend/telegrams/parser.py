from abc import ABC, abstractmethod
from datetime import datetime as dt
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.conf import settings

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

    @staticmethod
    def adjust_water_level_value_for_negative(value: int) -> int:
        """
        Adjusts the value if it's over 5000 to represent negative value.
        """
        return value if value <= 5000 else 5000 - value

    def parse_section_zero(self) -> dict[str, str | dt]:
        """
        Parses section 0 of the KN15 telegram.
        Section 0 contains the station code, date, and section code.
        """
        station_code = self.get_next_token()
        self.validate_station(station_code)

        def extract_day_from_token(date_token: str) -> int:
            try:
                day_in_month = int(date_token[:2])
                if not (1 <= day_in_month <= 31):
                    raise InvalidTokenException(f"Invalid day: {day_in_month}")
            except ValueError:
                raise InvalidTokenException(f"Invalid day: {date_token[:2]}")

            return day_in_month

        def extract_hour_from_token(date_token: str) -> int:
            try:
                hour = int(date_token[2:4])
                if not (0 <= hour <= 24):
                    raise InvalidTokenException(f"Invalid hour: {hour}")
            except ValueError:
                raise InvalidTokenException(f"Invalid hour: {date_token[2:4]}")

            return hour

        def determine_date(day_in_month: int, hour: int) -> dt:
            today = dt.now(tz=ZoneInfo(settings.TIME_ZONE))
            current_year, current_month = today.year, today.month

            # try setting the day of the current month to day_in_month
            try:
                parsed_date = dt(current_year, current_month, day_in_month, hour)
            except ValueError:
                # if day_in_month is invalid for the current month,
                # set parsed_date to the last day of the previous month
                if current_month == 1:  # if January, move to December of the previous year
                    parsed_date = dt(current_year - 1, 12, 31, hour)
                else:
                    last_day_prev_month = (dt(current_year, current_month, 1) - timedelta(days=1)).day
                    parsed_date = dt(current_year, current_month - 1, last_day_prev_month, hour)

            # if parsed_date is in the future, move it to the previous month
            if parsed_date > today:
                if parsed_date.month == 1:  # if January, move to December of the previous year
                    parsed_date = parsed_date.replace(year=parsed_date.year - 1, month=12)
                else:
                    parsed_date = parsed_date.replace(month=parsed_date.month - 1)

            # set the time to the given hour and zero out minutes, seconds and microseconds
            parsed_date = parsed_date.replace(minute=0, second=0, microsecond=0)

            return parsed_date

        input_token = self.get_next_token()
        parsed_day_in_month = extract_day_from_token(input_token)
        parsed_hour = extract_hour_from_token(input_token)
        date = determine_date(parsed_day_in_month, parsed_hour)

        try:
            section_code = int(input_token[4])
        except ValueError:
            raise InvalidTokenException(f"Invalid hour: {input_token[4]}")

        return {"station_code": station_code, "date": date, "section_code": section_code}

    def parse_section_one(self) -> dict:
        """
        Parses section 1 of the KN15 telegram.
        """

        def extract_water_level(token: str, starting_character: str) -> int:
            if not token.startswith(starting_character):
                raise InvalidTokenException(f"Expected token starting with '{starting_character}', got: {token}")
            water_level = self.adjust_water_level_value_for_negative(int(token[1:]))

            return water_level

        def extract_water_level_trend(token: str) -> int:
            if not token.startswith("2"):
                raise InvalidTokenException(f"Expected token starting with '2', got: {token}")

            trend = int(token[1:4])
            trend_sign = int(token[4])
            if trend_sign == 2:  # trend is negative
                trend = -trend

            return trend

        def extract_water_and_air_temperatures(token: str) -> tuple[float, int]:
            water_temp = int(token[1:3]) / 10
            air_temp = int(token[3:])

            if air_temp > 50:
                air_temp = air_temp - 50
                air_temp = -air_temp

            return water_temp, air_temp

        def extract_ice_phenomena(token: str) -> dict[str, int]:
            ice_phenomena_code = int(token[1:3])
            intensity = int(token[3:])
            if ice_phenomena_code == intensity:
                return {"code": ice_phenomena_code}
            else:
                return {"code": ice_phenomena_code, "intensity": intensity}

        # water level at 08:00
        input_token = self.get_next_token()
        morning_water_level = extract_water_level(input_token, "1")

        # water level trend
        input_token = self.get_next_token()
        water_level_trend = extract_water_level_trend(input_token)

        # water level at 20:00
        input_token = self.get_next_token()
        evening_water_level = extract_water_level(input_token, "3")

        # water and air temperatures - optional
        water_temperature, air_temperature = None, None
        if self.tokens and self.tokens[0].startswith("4"):
            input_token = self.get_next_token()
            water_temperature, air_temperature = extract_water_and_air_temperatures(input_token)

        # ice phenomena
        ice_phenomena = []
        while self.tokens and self.tokens[0].startswith("5"):
            input_token = self.get_next_token()
            ice_phenomena.append(extract_ice_phenomena(input_token))

        return {
            "morning_water_level": morning_water_level,
            "water_level_trend": water_level_trend,
            "evening_water_level": evening_water_level,
            "water_temperature": water_temperature,
            "air_temperature": air_temperature,
            "ice_phenomena": ice_phenomena,
        }

    def parse_section_three(self) -> int:
        """
        Parses section 3 of the KN15 telegram.
        """

        def extract_mean_water_level(token: str) -> int:
            if not token.startswith("1"):
                raise InvalidTokenException(f"Expected token starting with '1', got: {token}")

            mean_water_level = self.adjust_water_level_value_for_negative(int(token[1:]))

            return mean_water_level

        # mean water level for the period 20:00 to 08:00
        input_token = self.get_next_token()
        parsed_mean_water_level = extract_mean_water_level(input_token)

        # skip any additional tokens until we reach the next section or end of telegram
        while self.tokens and not self.tokens[0].startswith("9"):
            self.get_next_token()

        return parsed_mean_water_level

    def parse_section_six(self) -> dict:
        """
        Parses section 6 of the KN15 telegram.
        """

        def extract_discharge_or_free_river_area(token: str) -> int:
            significand = int(token[2:])
            exponent = int(token[1])
            return significand * (10 ** (exponent - 3))

        # group 966MM
        input_token = self.get_next_token()
        month = int(input_token[3:])

        # group 1HHHH
        input_token = self.get_next_token()
        water_level = self.adjust_water_level_value_for_negative(int(input_token[1:]))

        # group 2kQQQ
        input_token = self.get_next_token()
        discharge = extract_discharge_or_free_river_area(input_token)

        # group 3kFFF (optional)
        free_river_area = None
        if self.tokens and self.tokens[0].startswith("3"):
            input_token = self.get_next_token()
            free_river_area = extract_discharge_or_free_river_area(input_token)

        # group 4hhhh (optional)
        maximum_depth = None
        if self.tokens and self.tokens[0].startswith("4"):
            token = self.get_next_token()
            maximum_depth = int(token[1:])

        # group 5YYGG
        token = self.get_next_token()
        day_in_month = int(token[1:3])
        hour = int(token[3:])

        # Calculate the date
        today = dt.now(tz=ZoneInfo(settings.TIME_ZONE))
        date = dt(today.year, month, day_in_month, hour)
        if date > today:
            date = date.replace(year=date.year - 1)

        # Skip additional tokens until section end
        while self.tokens and not self.tokens[0].startswith("9"):
            self.get_next_token()

        return {
            "water_level": water_level,
            "discharge": discharge,
            "free_river_area": free_river_area,
            "maximum_depth": maximum_depth,
            "date": date,
        }
