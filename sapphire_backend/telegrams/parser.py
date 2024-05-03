from abc import ABC, abstractmethod
from datetime import datetime as dt
from datetime import timedelta
from typing import Any

from django.conf import settings
from zoneinfo import ZoneInfo

from sapphire_backend.stations.models import HydrologicalStation, MeteorologicalStation
from sapphire_backend.telegrams.exceptions import (
    InvalidTokenException,
    MissingMeteoStationException,
    MissingSectionException,
    TelegramParserException,
    UnsupportedSectionException,
)
from sapphire_backend.telegrams.models import Telegram


class BaseTelegramParser(ABC):
    def __init__(
        self, telegram: str, organization_uuid, store_parsed_telegram: bool = True, automatic_ingestion: bool = False
    ):
        self.original_telegram = telegram.strip()
        self.telegram = self.handle_telegram_termination_character()
        self.store_in_db = store_parsed_telegram
        self.automatic_ingestion = automatic_ingestion
        self.tokens = self.tokenize()
        self.organization_uuid = organization_uuid
        self.hydro_station = None
        self.meteo_station = None
        self.validate_format()

    @property
    def exists_hydro_station(self):
        return self.hydro_station is not None

    @property
    def exists_meteo_station(self):
        return self.meteo_station is not None

    def handle_telegram_termination_character(self, termination_character: str = "="):
        return (
            self.original_telegram[:-1]
            if self.original_telegram.endswith(termination_character)
            else self.original_telegram
        )

    def validate_format(self):
        """
        Used to validate the format of the telegram if necessary
        """
        return True

    def telegram_already_parsed(self):
        return Telegram.objects.filter(telegram=self.original_telegram, successfully_parsed=True).exists()

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
        # TODO think about this,
        # can lead to issues in very rare some edge cases
        # if self.telegram_already_parsed():
        #    raise TelegramAlreadyParsedException(telegram=self.original_telegram)
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
        self.save_parsing_error("Unexpected end of telegram", self.telegram, MissingSectionException)

    def validate_station(self, station_code: str) -> None:
        if not station_code.isdigit() or len(station_code) != 5:
            self.save_parsing_error("Invalid station code", station_code, InvalidTokenException)

        self.hydro_station = HydrologicalStation.objects.filter(
            site__organization_id=self.organization_uuid,
            station_code=station_code,
            station_type=HydrologicalStation.StationType.MANUAL,
        ).first()
        self.meteo_station = MeteorologicalStation.objects.filter(
            site__organization_id=self.organization_uuid, station_code=station_code
        ).first()
        if self.hydro_station is None and self.meteo_station is None:
            # except HydrologicalStation.DoesNotExist:
            self.save_parsing_error(
                "No manual hydro or meteo station with the following code", station_code, InvalidTokenException
            )

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
            hydro_station=self.hydro_station,
            meteo_station=self.meteo_station,
        )

    def save_parsing_error(
        self, error: str, token: str | int = "", exception_class: TelegramParserException | None = None
    ):
        Telegram.objects.create(
            telegram=self.original_telegram,
            automatically_ingested=self.automatic_ingestion,
            hydro_station=self.hydro_station,
            meteo_station=self.meteo_station,
            errors=f"{error}: {token}",
            successfully_parsed=False,
        )
        if exception_class:
            raise exception_class(token, error)


class KN15TelegramParser(BaseTelegramParser):
    def __init__(
        self,
        telegram: str,
        organization_uuid: str,
        store_parsed_telegram: bool = True,
        automatic_ingestion: bool = False,
    ):
        super().__init__(telegram, organization_uuid, store_parsed_telegram, automatic_ingestion)

    def validate_format(self):
        if self.tokens[1][-1] not in ["1", "2"]:
            self.save_parsing_error("Group must end with either 1 or 2", self.tokens[1], InvalidTokenException)

        for token in self.tokens:
            if len(token) != 5:
                self.save_parsing_error("Group must have 5 characters", token, InvalidTokenException)

            if token[:3] in ["933", "966", "988"]:
                if self.tokens[1][-1] != "2":
                    self.save_parsing_error(
                        f"Found the following token, but group {self.tokens[1]} doesn't end with 2",
                        token,
                        InvalidTokenException,
                    )

    def parse(self):
        """
        Implements the parsing logic for KN15 telegrams.
        """
        super().parse()
        decoded_values = {}
        # start by parsing section zero
        section_zero = self.parse_section_zero()
        decoded_values["section_zero"] = section_zero
        decoded_values["section_three"] = {}
        decoded_values["section_six"] = []
        decoded_values["section_eight"] = {}

        if section_zero["section_code"] == 1:
            section_one = self.parse_section_one()
            decoded_values["section_one"] = section_one

        elif section_zero["section_code"] == 2:
            section_one = self.parse_section_one()
            decoded_values["section_one"] = section_one
            while self.tokens:
                token = self.tokens[0]
                section_number = token[:3]

                if section_number == "933":
                    section_three = self.parse_section_three()
                    decoded_values["section_three"] = section_three
                elif section_number == "966":
                    section_six = self.parse_section_six()
                    decoded_values["section_six"].append(section_six)
                elif section_number == "988":
                    section_eight = self.parse_section_eight()
                    decoded_values["section_eight"] = section_eight
                else:
                    raise UnsupportedSectionException(section_number, "Unsupported section number inside section 1")

        else:
            self.save_parsing_error(
                "Unsupported section code (only 1 and 2 are allowed), got",
                section_zero["section_code"],
                UnsupportedSectionException,
            )

        # remove sections three and six if they are still empty
        if not decoded_values["section_three"]:
            decoded_values.pop("section_three")
        if not decoded_values["section_six"]:
            decoded_values.pop("section_six")
        if not decoded_values["section_eight"]:
            decoded_values.pop("section_eight")

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
        section_eight_data = decoded_values.get("section_eight")
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

        if section_eight_data:
            print("\nDecadal / monthly precipitation and temperature (988)")
            print(f"\nDecade: {section_eight_data.get('decade')}")
            print(f"\nTimestamp for the given decade: {section_eight_data.get('timestamp')}")
            print(f"\nPrecipitation: {section_eight_data.get('precipitation')} mm")
            print(f"\nTemperature: {section_eight_data.get('temperature')} °C")

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
                    self.save_parsing_error(
                        f"Invalid day in month for token {date_token}", day_in_month, InvalidTokenException
                    )
                return day_in_month
            except ValueError:
                self.save_parsing_error(
                    f"Invalid day in month for token {date_token}", date_token[:2], InvalidTokenException
                )

        def extract_hour_from_token(date_token: str) -> int:
            try:
                hour = int(date_token[2:4])
                if not (0 <= hour <= 24):
                    self.save_parsing_error(f"Invalid hour for token {date_token}", hour, InvalidTokenException)
                return hour
            except ValueError:
                self.save_parsing_error(f"Invalid hour for token {date_token}", date_token[2:4], InvalidTokenException)

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
                    try:
                        parsed_date = parsed_date.replace(month=parsed_date.month - 1)
                    except ValueError:  # could fall into 31st which might not exist for the previous month
                        last_day_prev_month = (dt(parsed_date.year, parsed_date.month, 1) - timedelta(days=1)).day
                        parsed_date = parsed_date.replace(month=parsed_date.month - 1, day=last_day_prev_month)

            # set the time to the given hour and zero out minutes, seconds and microseconds
            parsed_date = parsed_date.replace(minute=0, second=0, microsecond=0)

            return parsed_date

        input_token = self.get_next_token()
        parsed_day_in_month = extract_day_from_token(input_token)
        parsed_hour = extract_hour_from_token(input_token)
        date = determine_date(parsed_day_in_month, parsed_hour)

        section_code = int(input_token[4])

        return {
            "station_code": station_code,
            "station_name": getattr(self.hydro_station, "name", None) or getattr(self.meteo_station, "name", None),
            "date": date.isoformat(),
            "section_code": section_code,
        }

    def parse_section_one(self) -> dict:
        """
        Parses section 1 of the KN15 telegram.
        """

        def extract_water_level(token: str, starting_character: str) -> int:
            if not token.startswith(starting_character):
                self.save_parsing_error(
                    f"Expected token starting with '{starting_character}', got", token, InvalidTokenException
                )
            water_level = self.adjust_water_level_value_for_negative(int(token[1:]))

            return water_level

        def extract_water_level_trend(token: str) -> int:
            if not token.startswith("2"):
                self.save_parsing_error("Expected token starting with '2', got", token, InvalidTokenException)

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

        def extract_daily_precipitation(token: str) -> dict[str, int]:
            precipitation_mm = int(token[1:4])
            if precipitation_mm > 989:
                precipitation_mm = (precipitation_mm - 990) / 10
            duration_code = int(token[4])
            return {"precipitation": precipitation_mm, "duration_code": duration_code}

        # water level at 08:00
        input_token = self.get_next_token()

        if not self.exists_hydro_station:
            self.save_parsing_error(
                f"No hydro station with code {self.meteo_station.station_code}, but found token",
                input_token,
                InvalidTokenException,
            )
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

        daily_precipitation = None
        if self.tokens and self.tokens[0].startswith("0"):
            input_token = self.get_next_token()
            daily_precipitation = extract_daily_precipitation(input_token)

        return {
            "morning_water_level": morning_water_level,
            "water_level_trend": water_level_trend,
            "water_level_20h_period": water_level_over_20h_period,
            "water_temperature": water_temperature,
            "air_temperature": air_temperature,
            "ice_phenomena": ice_phenomena,
            "daily_precipitation": daily_precipitation,
        }

    def parse_section_three(self) -> dict[str, int | float]:
        """
        Parses section 3 of the KN15 telegram.
        """

        def extract_mean_water_level(token: str) -> int:
            if not token.startswith("1"):
                self.save_parsing_error("Expected token starting with '1', got", token, InvalidTokenException)

            mean_water_level = self.adjust_water_level_value_for_negative(int(token[1:]))

            return mean_water_level

        # check if the information refers to the previous day which is currently supported
        input_token = self.get_next_token()
        if not input_token.endswith("01"):
            self.save_parsing_error(
                "Expected data from previous day (code 93301), got", input_token, InvalidTokenException
            )

        # mean water level for the period 20:00 to 08:00
        input_token = self.get_next_token()
        parsed_mean_water_level = extract_mean_water_level(input_token)

        while self.tokens and not self.tokens[0].startswith("9"):
            self.get_next_token()

        return {"water_level": parsed_mean_water_level}

    def parse_section_six(self) -> dict:
        """
        Parses section 6 of the KN15 telegram.
        """

        def extract_discharge_or_free_river_area(token: str) -> float:
            significand = int(token[2:])
            exponent = int(token[1])
            return round(significand * (10 ** (exponent - 3)), 4)

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

    def parse_section_eight(self) -> dict:
        def extract_decade_number(token: str) -> int:
            if not token.startswith("1"):
                self.save_parsing_error(
                    "Expected decade section starting with '1', got", token, MissingSectionException
                )
            match token[1:3]:
                case "11":
                    return 1
                case "22":
                    return 2
                case "33":
                    return 3
                case "30":
                    return 4  # special case, means full month, not a decade
                case _:
                    self.save_parsing_error(
                        "Invalid decade identifier, supported identifiers are '11', '22', '33' and '30'",
                        token,
                        InvalidTokenException,
                    )

        def extract_precipitation(token: str) -> int:
            if not token.startswith("2"):
                self.save_parsing_error(
                    "Expected precipitation section starting with '2', got", token, MissingSectionException
                )
            precipitation_value = int(token[1:4])
            check_digit = token[-1]
            digit_sum = sum(int(char) for char in token[:4])

            if digit_sum != int(check_digit):
                self.save_parsing_error("Check digit sum does not match", token, InvalidTokenException)

            return precipitation_value

        def extract_temperature(token: str) -> float:
            if not token.startswith("3"):
                self.save_parsing_error(
                    "Expected temperature section starting with '3', got", token, MissingSectionException
                )
            match token[1]:
                case "0":
                    sign = 1
                case "1":
                    sign = -1
                case _:
                    self.save_parsing_error("Invalid second digit, expected '0' or '1'", token, InvalidTokenException)

            temperature_value = round(int(token[2:]) * 0.1, 1)
            return temperature_value * sign

        def get_day_in_month_for_decade(decade_num: int) -> int:
            match decade_num:
                case 1:
                    return 5
                case 2:
                    return 15
                case 3:
                    return 25
                case _:
                    # monthly data, not decadal
                    return 15

        # group 988mm
        input_token = self.get_next_token()
        month = int(input_token[3:])

        if not self.exists_meteo_station:
            self.save_parsing_error(
                f"No meteo station with code {self.hydro_station.station_code}, but found token",
                input_token,
                MissingMeteoStationException,
            )

        # subgroup 1dd//
        input_token = self.get_next_token()
        decade = extract_decade_number(input_token)

        # subgroup 2pppc
        input_token = self.get_next_token()
        precipitation = extract_precipitation(input_token)

        # subgroup 3sttt
        input_token = self.get_next_token()
        temperature = extract_temperature(input_token)

        day_in_month = get_day_in_month_for_decade(decade)
        timestamp = dt(year=dt.now().year, month=month, day=day_in_month, hour=12, tzinfo=ZoneInfo("UTC"))

        # Skip additional tokens until section end
        while self.tokens and not self.tokens[0].startswith("9"):
            self.get_next_token()

        return {
            "decade": decade,
            "timestamp": timestamp.isoformat(),
            "precipitation": precipitation,
            "temperature": temperature,
        }
