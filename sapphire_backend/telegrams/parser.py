from abc import ABC, abstractmethod
from datetime import datetime as dt
from datetime import timedelta
from typing import Any
from zoneinfo import ZoneInfo

from django.conf import settings

from sapphire_backend.stations.models import Station
from sapphire_backend.telegrams.exceptions import (
    InvalidTokenException,
    MissingSectionException,
    UnsupportedSectionException,
)
from sapphire_backend.telegrams.models import Telegram


class BaseTelegramParser(ABC):
    def __init__(self, telegram: str, store_parsed_telegram: bool = True, automatic_ingestion: bool = False):
        self.original_telegram = telegram.strip()
        self.telegram = self.handle_telegram_termination_character()
        self.store_in_db = store_parsed_telegram
        self.automatic_ingestion = automatic_ingestion
        self.tokens = self.tokenize()
        self.station = None

    def handle_telegram_termination_character(self, termination_character: str = "="):
        return (
            self.original_telegram[:-1]
            if self.original_telegram.endswith(termination_character)
            else self.original_telegram
        )

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

    @staticmethod
    def print_decoded_telegram(decoded_values: dict[str, Any]):
        print(decoded_values)

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
        raise MissingSectionException("Unexpected end of telegram")

    def validate_station(self, station_code: str) -> None:
        if not station_code.isdigit() or len(station_code) != 5:
            raise InvalidTokenException(f"Invalid station code: {station_code}")
        try:
            self.station = Station.objects.get(station_code=station_code)
        except Station.DoesNotExist:
            raise InvalidTokenException(f"Station with code {station_code} does not exist")

    @classmethod
    def parse_bulk(cls, telegrams: list[str], store_in_db: bool = False, automatic: bool = False) -> list:
        """
        Parses a list of telegrams and returns a list of parsed results.
        """
        return [cls(telegram, store_in_db, automatic).parse() for telegram in telegrams]

    def save_telegram(self, decoded_values: dict[str, Any]):
        Telegram.objects.create(
            telegram=self.original_telegram,
            decoded_values=decoded_values,
            automatically_ingested=self.automatic_ingestion,
            organization=self.station.organization,
        )


class KN15TelegramParser(BaseTelegramParser):
    def __init__(self, telegram: str, store_parsed_telegram: bool = True, automatic_ingestion: bool = False):
        super().__init__(telegram, store_parsed_telegram, automatic_ingestion)

    def parse(self):
        """
        Implements the parsing logic for KN15 telegrams.
        """
        decoded_values = {}
        # start by parsing section zero
        section_zero = self.parse_section_zero()
        decoded_values["section_zero"] = section_zero

        if section_zero["section_code"] == 1:
            section_one = self.parse_section_one()
            decoded_values["section_one"] = section_one

        elif section_zero["section_code"] == 2:
            section_one = self.parse_section_one()
            decoded_values["section_one"] = section_one
            decoded_values["section_three"] = []
            decoded_values["section_six"] = []
            while self.tokens:
                token = self.tokens[0]
                section_number = token[:3]

                if section_number == "933":
                    section_three = self.parse_section_three()
                    decoded_values["section_three"].append(section_three)
                elif section_number == "966":
                    section_six = self.parse_section_six()
                    decoded_values["section_six"].append(section_six)
                else:
                    raise UnsupportedSectionException(section_number, "Unsupported section number inside section 1")

        else:
            raise UnsupportedSectionException(
                section_zero["section_code"], "Unsupported section code (only 1 and 2 are allowed), got"
            )

        # remove sections three and six if they are still empty
        if not decoded_values["section_three"]:
            decoded_values.pop("section_three")
        if not decoded_values["section_six"]:
            decoded_values.pop("section_six")

        if self.store_in_db:
            self.save_telegram(decoded_values)
        else:
            self.print_decoded_telegram(decoded_values)

        return decoded_values

    @staticmethod
    def print_decoded_telegram(decoded_values: dict[str, Any]):
        section_one = decoded_values.get("section_one")
        section_three_list = decoded_values.get("section_three")
        section_six_list = decoded_values.get("section_six")
        section_zero_date = dt.fromisoformat(decoded_values["section_zero"]["date"])
        previous_day = section_zero_date - timedelta(days=1)
        morning_water_level = None
        daily_change = None

        print("Reported water level")
        print("Previous day")
        print(f"{previous_day.strftime('%B %d, %Y')}")

        if section_one:
            morning_water_level = section_one.get("morning_water_level")
            water_level_20h_period = section_one.get("water_level_20h_period")
            daily_change = section_one.get("water_level_trend")

            print("\n8:00 AM")
            print("--- cm" if morning_water_level is None else f"{morning_water_level} cm")

            print("\n8:00 PM")
            print("--- cm" if water_level_20h_period is None else f"{water_level_20h_period} cm")

            print("\nDaily average")
            print("--- cm")

        print(f"\nTelegram day\n{section_zero_date.strftime('%B %d, %Y')}")
        print("\n8:00 AM")
        print(f"{morning_water_level} cm" if morning_water_level else "--- cm")

        print(f"\nDaily change\n{daily_change} cm")

        if section_three_list:
            for section_three in section_three_list:
                mean_water_level = section_three.get("mean_water_level")
                print("\nReported mean water level")
                print(f"{mean_water_level} cm" if mean_water_level else "--- cm")

        if section_six_list:
            for section_six in section_six_list:
                date = dt.fromisoformat(section_six.get("date"))
                water_level = section_six.get("water_level")
                cross_section_area = section_six.get("cross_section_area")
                discharge = section_six.get("discharge")
                maximum_depth = section_six.get("maximum_depth")

                print("\nwarning")
                print("Reported discharge")
                print(f"Date\n{date.strftime('%B %d, %Y')}")

                print(f"\nWater level\n{water_level} cm" if water_level else "--- cm")
                print(f"\nCross-section area\n{cross_section_area} m2" if cross_section_area else "--- m2")
                print(f"\nDischarge\n{discharge} m3/s" if discharge else "--- m3/s")
                print(f"\nMaximum depth\n{maximum_depth} cm" if maximum_depth else "--- cm")

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
                parsed_date = dt(current_year, current_month, day_in_month, hour, tzinfo=ZoneInfo(settings.TIME_ZONE))
            except ValueError:
                # if day_in_month is invalid for the current month,
                # set parsed_date to the last day of the previous month
                if current_month == 1:  # if January, move to December of the previous year
                    parsed_date = dt(current_year - 1, 12, 31, hour, tzinfo=ZoneInfo(settings.TIME_ZONE))
                else:
                    last_day_prev_month = (dt(current_year, current_month, 1) - timedelta(days=1)).day
                    parsed_date = dt(
                        current_year, current_month - 1, last_day_prev_month, hour, tzinfo=ZoneInfo(settings.TIME_ZONE)
                    )

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

        return {"station_code": station_code, "date": date.isoformat(), "section_code": section_code}

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
        water_level_over_20h_period = extract_water_level(input_token, "3")

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
            "water_level_20h_period": water_level_over_20h_period,
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

        # check if the information refers to the previous day which is currently supported
        input_token = self.get_next_token()
        if not input_token.endswith("01"):
            raise InvalidTokenException(f"Expected data from previous day (code 93301), got: {input_token}")

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

        def extract_discharge_or_free_river_area(token: str) -> float:
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
        cross_section_area = None
        if self.tokens and self.tokens[0].startswith("3"):
            input_token = self.get_next_token()
            cross_section_area = extract_discharge_or_free_river_area(input_token)

        # group 4hhhh (optional)
        maximum_depth = None
        if self.tokens and self.tokens[0].startswith("4"):
            input_token = self.get_next_token()
            maximum_depth = int(input_token[1:])

        # group 5YYGG
        input_token = self.get_next_token()
        day_in_month = int(input_token[1:3])
        hour = int(input_token[3:])

        # Calculate the date
        today = dt.now(tz=ZoneInfo(settings.TIME_ZONE))
        date = dt(today.year, month, day_in_month, hour, tzinfo=ZoneInfo(settings.TIME_ZONE))
        if date > today:
            date = date.replace(year=date.year - 1)

        # Skip additional tokens until section end
        while self.tokens and not self.tokens[0].startswith("9"):
            self.get_next_token()

        return {
            "water_level": water_level,
            "discharge": discharge,
            "cross_section_area": cross_section_area,
            "maximum_depth": maximum_depth,
            "date": date.isoformat(),
        }
