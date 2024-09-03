import datetime
import re
from unittest.mock import patch

import pytest
from zoneinfo import ZoneInfo

from sapphire_backend.telegrams.exceptions import (
    InvalidTokenException,
    MissingMeteoStationException,
    MissingSectionException,
)
from sapphire_backend.telegrams.models import TelegramParserLog
from sapphire_backend.telegrams.parser import KN15TelegramParser


class TestKN15TelegramParserInitialization:
    def test_strip_whitespaces(self, organization):
        parser = KN15TelegramParser("     12345 29081 10417 20021 30410=     ", organization.uuid)

        assert parser.original_telegram == "12345 29081 10417 20021 30410="

    def test_handle_termination_character(self, organization):
        parser = KN15TelegramParser("12345 29081 10417 20021 30410=", organization.uuid)
        assert parser.telegram == "12345 29081 10417 20021 30410"

        # Test without termination character
        parser_no_termination = KN15TelegramParser("12345 29081 10417 20021 30410=", organization.uuid)
        assert parser_no_termination.telegram == "12345 29081 10417 20021 30410"

    def test_tokenization(self, organization):
        parser = KN15TelegramParser("12345 29081 10417 20021 30410=", organization.uuid)
        expected_tokens = ["12345", "29081", "10417", "20021", "30410"]
        assert parser.tokens == expected_tokens

    def test_initial_parameter_assignment(self, organization):
        parser = KN15TelegramParser("12345 29081 10417 20021 30410=", organization.uuid, False, True)
        assert not parser.store_in_db
        assert parser.automatic_ingestion
        assert parser.organization_uuid == organization.uuid

    def test_get_next_token(self, organization):
        parser = KN15TelegramParser("12345 29081 10417 20021 30410=", organization.uuid)

        assert parser.get_next_token() == "12345"
        assert parser.get_next_token() == "29081"
        assert parser.get_next_token() == "10417"
        assert parser.get_next_token() == "20021"
        assert parser.get_next_token() == "30410"

    def test_get_next_token_after_end_of_telegram(self, organization):
        parser = KN15TelegramParser("12345 29081", organization.uuid)

        assert parser.get_next_token() == "12345"
        assert parser.get_next_token() == "29081"

        with pytest.raises(MissingSectionException, match="Unexpected end of telegram: 12345 29081"):
            parser.get_next_token()

    def test_hydro_station_property(self, organization, manual_hydro_station):
        parser = KN15TelegramParser(f"{manual_hydro_station.station_code} 29081 10417 20021 30410=", organization.uuid)
        parser.parse()
        assert parser.exists_hydro_station
        assert not parser.exists_meteo_station

    def test_meteo_station_property(self, organization, manual_hydro_station, manual_meteo_station):
        parser = KN15TelegramParser(f"{manual_hydro_station.station_code} 29081 10417 20021 30410=", organization.uuid)
        parser.parse()
        assert parser.exists_hydro_station
        assert parser.exists_meteo_station

    def test_parse_error_stores_telegram_to_database(self, organization, manual_hydro_station):
        parser = KN15TelegramParser(f"{manual_hydro_station.station_code} 29081 10417 30410=", organization.uuid)

        assert TelegramParserLog.objects.exists() is False

        expected_exception = "Expected token starting with '2', got: 30410"

        with pytest.raises(InvalidTokenException, match=expected_exception):
            parser.parse()
            db_telegram = TelegramParserLog.objects.first()
            assert db_telegram.errors == expected_exception
            assert db_telegram.valid is False


class TestKN15TelegramParserSectionZero:
    def test_parse_with_invalid_station_code(self, organization):
        parser = KN15TelegramParser("abcde 29081 10417 20021 30410=", organization.uuid)

        with pytest.raises(InvalidTokenException, match="Invalid station code: abcde"):
            parser.parse()

        with pytest.raises(InvalidTokenException, match="Group must have 5 characters: 123456"):
            _ = KN15TelegramParser("123456 29081 10417 20021 30410=", organization.uuid)

    def test_parse_with_invalid_last_digit_in_the_second_group(self, organization, manual_hydro_station):
        with pytest.raises(InvalidTokenException, match="Group must end with either 1 or 2: 29083"):
            _ = KN15TelegramParser(f"{manual_hydro_station.station_code} 29083 10417 20021 30410=", organization.uuid)

    def test_parse_for_non_existing_station(self, organization):
        parser = KN15TelegramParser("12345 29081 10417 20021 30410=", organization.uuid)
        with pytest.raises(
            InvalidTokenException, match="No manual hydro or meteo station with the following code: 12345"
        ):
            parser.parse()

    def test_parse_for_automatic_station(self, organization, automatic_hydro_station):
        parser = KN15TelegramParser(
            f"{automatic_hydro_station.station_code} 29081 10417 20021 30410=", organization.uuid
        )
        with pytest.raises(
            InvalidTokenException,
            match=f"No manual hydro or meteo station with the following code: {automatic_hydro_station.station_code}",
        ):
            parser.parse()

    def test_parse_for_invalid_day(self, organization, manual_hydro_station):
        parser = KN15TelegramParser(f"{manual_hydro_station.station_code} 32081 10417 20021 30410=", organization.uuid)
        with pytest.raises(InvalidTokenException, match="Invalid day in month for token 32081: 32"):
            parser.parse()

        parser = KN15TelegramParser(f"{manual_hydro_station.station_code} ab081 10417 20021 30410=", organization.uuid)
        with pytest.raises(InvalidTokenException, match="Invalid day in month for token ab081: ab"):
            parser.parse()

    def test_parse_for_invalid_hour(self, organization, manual_hydro_station):
        parser = KN15TelegramParser(f"{manual_hydro_station.station_code} 30251 10417 20021 30410=", organization.uuid)

        with pytest.raises(InvalidTokenException, match="Invalid hour for token 30251: 25"):
            parser.parse()

    @patch("sapphire_backend.telegrams.parser.dt")
    def test_parse_for_invalid_date_rollback_invalid_day(
        self, mock_datetime, organization_kyrgyz, manual_hydro_station_kyrgyz
    ):
        # April has 30 days
        mock_datetime.now.return_value = datetime.datetime(2024, 4, 30, tzinfo=ZoneInfo("UTC"))
        mock_datetime.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)

        # 31081 means day 31 which is invalid for April
        parser = KN15TelegramParser(
            f"{manual_hydro_station_kyrgyz.station_code} 31081 10417 20021 30410=", organization_kyrgyz.uuid
        )
        decoded_values = parser.parse()
        assert decoded_values["section_zero"]["date"] == "2024-03-31T08:00:00+06:00"

    @patch("sapphire_backend.telegrams.parser.dt")
    def test_parse_for_future_date_rollback_with_day_shift(
        self, mock_datetime, organization_kyrgyz, manual_hydro_station_kyrgyz
    ):
        # May has 31 days
        mock_datetime.now.return_value = datetime.datetime(2024, 5, 30, tzinfo=ZoneInfo("UTC"))
        mock_datetime.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)

        # 31081 means day 31 which is a day in the future since the mocked today is the 30th,
        # so we assume the date should be in the previous month
        # and since April doesn't have 31 days, we shift the day for 1 as well
        parser = KN15TelegramParser(
            f"{manual_hydro_station_kyrgyz.station_code} 31081 10417 20021 30410=", organization_kyrgyz.uuid
        )
        decoded_values = parser.parse()
        assert decoded_values["section_zero"]["date"] == "2024-04-30T08:00:00+06:00"

    @patch("sapphire_backend.telegrams.parser.dt")
    def test_parse_for_future_date_rollback_without_day_shift(
        self, mock_datetime, organization_kyrgyz, manual_hydro_station_kyrgyz
    ):
        # April has 30 days
        mock_datetime.now.return_value = datetime.datetime(2024, 4, 20, tzinfo=ZoneInfo("UTC"))
        mock_datetime.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)

        # 25081 means day 25 which is a day in the future since the mocked today is the 20th,
        # so we assume the date should be in the previous month
        parser = KN15TelegramParser(
            f"{manual_hydro_station_kyrgyz.station_code} 25081 10417 20021 30410=", organization_kyrgyz.uuid
        )
        decoded_values = parser.parse()
        assert decoded_values["section_zero"]["date"] == "2024-03-25T08:00:00+06:00"

    @patch("sapphire_backend.telegrams.parser.dt")
    def test_parse_for_date_new_year_rollback(self, mock_datetime, organization_kyrgyz, manual_hydro_station_kyrgyz):
        mock_datetime.now.return_value = datetime.datetime(2024, 1, 20, tzinfo=ZoneInfo("UTC"))
        mock_datetime.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)

        parser = KN15TelegramParser(
            f"{manual_hydro_station_kyrgyz.station_code} 25081 10417 20021 30410=", organization_kyrgyz.uuid
        )

        decoded_values = parser.parse()
        assert decoded_values["section_zero"]["date"] == "2023-12-25T08:00:00+06:00"

    @patch("sapphire_backend.telegrams.parser.dt")
    def test_parse_for_date_leap_year_feb(self, mock_datetime, organization_kyrgyz, manual_hydro_station_kyrgyz):
        mock_datetime.now.return_value = datetime.datetime(2024, 3, 1, tzinfo=ZoneInfo("UTC"))
        mock_datetime.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)

        parser = KN15TelegramParser(
            f"{manual_hydro_station_kyrgyz.station_code} 30081 10417 20021 30410=", organization_kyrgyz.uuid
        )

        decoded_values = parser.parse()
        assert decoded_values["section_zero"]["date"] == "2024-02-29T08:00:00+06:00"

    @patch("sapphire_backend.telegrams.parser.dt")
    def test_parse_for_date_non_leap_year_feb(self, mock_datetime, organization_kyrgyz, manual_hydro_station_kyrgyz):
        mock_datetime.now.return_value = datetime.datetime(2023, 3, 1, tzinfo=ZoneInfo("UTC"))
        mock_datetime.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)

        parser = KN15TelegramParser(
            f"{manual_hydro_station_kyrgyz.station_code} 30081 10417 20021 30410=", organization_kyrgyz.uuid
        )

        decoded_values = parser.parse()
        assert decoded_values["section_zero"]["date"] == "2023-02-28T08:00:00+06:00"

    @patch("sapphire_backend.telegrams.parser.dt")
    def test_parse_full_output(self, mock_datetime, organization_kyrgyz, manual_hydro_station_kyrgyz):
        mock_datetime.now.return_value = datetime.datetime(2024, 4, 15, tzinfo=ZoneInfo("UTC"))
        mock_datetime.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)

        parser = KN15TelegramParser(
            f"{manual_hydro_station_kyrgyz.station_code} 14081 10417 20021 30410=", organization_kyrgyz.uuid
        )

        decoded_values = parser.parse()
        assert decoded_values["section_zero"] == {
            "station_code": manual_hydro_station_kyrgyz.station_code,
            "station_name": manual_hydro_station_kyrgyz.name,
            "date": "2024-04-14T08:00:00+06:00",
            "section_code": 1,
        }

    def test_parsing_saves_telegram_to_database(self, datetime_mock, organization, manual_hydro_station):
        parser = KN15TelegramParser(f"{manual_hydro_station.station_code} 14081 10417 20021 30410=", organization.uuid)

        assert TelegramParserLog.objects.all().count() == 0

        decoded_data = parser.parse()

        db_telegrams = TelegramParserLog.objects.all()

        assert db_telegrams.count() == 1
        assert db_telegrams.first().decoded_values == decoded_data

    def test_parsing_doesnt_save_telegram_to_database_if_saving_disabled(
        self, datetime_mock, organization, manual_hydro_station
    ):
        parser = KN15TelegramParser(
            f"{manual_hydro_station.station_code} 14081 10417 20021 30410=",
            organization.uuid,
            store_parsed_telegram=False,
        )

        assert TelegramParserLog.objects.all().count() == 0

        _ = parser.parse()

        assert TelegramParserLog.objects.all().count() == 0


class TestKN15TelegramParserSectionOne:
    def test_parse_for_non_existing_manual_hydro_station(self, datetime_mock, organization, manual_meteo_station):
        parser = KN15TelegramParser(f"{manual_meteo_station.station_code} 14081 10417 20021 30410=", organization.uuid)

        with pytest.raises(
            InvalidTokenException,
            match=f"No hydro station with code {manual_meteo_station.station_code}, but found token: 10417",
        ):
            parser.parse()

    def test_parse_with_missing_morning_water_level(self, datetime_mock, organization, manual_hydro_station):
        parser = KN15TelegramParser(f"{manual_hydro_station.station_code} 14081 20021 30410=", organization.uuid)
        with pytest.raises(InvalidTokenException, match="Expected token starting with '1', got: 20021"):
            parser.parse()

    def test_parse_with_missing_water_level_trend(self, datetime_mock, organization, manual_hydro_station):
        parser = KN15TelegramParser(f"{manual_hydro_station.station_code} 14081 10417 30410=", organization.uuid)
        with pytest.raises(InvalidTokenException, match="Expected token starting with '2', got: 30410"):
            parser.parse()

    def test_parse_with_missing_evening_water_level(self, datetime_mock, organization, manual_hydro_station):
        parser = KN15TelegramParser(f"{manual_hydro_station.station_code} 14081 10417 20021=", organization.uuid)
        with pytest.raises(
            MissingSectionException,
            match=f"Unexpected end of telegram: {manual_hydro_station.station_code} 14081 10417 20021",
        ):
            parser.parse()

    def test_parse_with_missing_evening_water_level_with_extra_groups(
        self, datetime_mock, organization, manual_hydro_station
    ):
        parser = KN15TelegramParser(f"{manual_hydro_station.station_code} 14081 10417 20021 46510=", organization.uuid)
        with pytest.raises(InvalidTokenException, match="Expected token starting with '3', got: 46510"):
            parser.parse()

    def test_parse_with_only_basic_data(self, datetime_mock, organization, manual_hydro_station):
        parser = KN15TelegramParser(f"{manual_hydro_station.station_code} 14081 10417 20021 30410=", organization.uuid)

        decoded_data = parser.parse()

        assert decoded_data["section_one"] == {
            "morning_water_level": 417,
            "water_level_trend": 2,
            "water_level_20h_period": 410,
            "water_temperature": None,
            "air_temperature": None,
            "ice_phenomena": [],
            "daily_precipitation": None,
        }

    def test_parse_full_output(self, datetime_mock, organization, manual_hydro_station):
        parser = KN15TelegramParser(f"{manual_hydro_station.station_code} 14081 10417 20021 30410=", organization.uuid)

        decoded_data = parser.parse()

        assert decoded_data == {
            "raw": f"{manual_hydro_station.station_code} 14081 10417 20021 30410=",
            "section_zero": {
                "station_code": manual_hydro_station.station_code,
                "station_name": manual_hydro_station.name,
                "date": "2024-04-14T08:00:00+00:00",
                "section_code": 1,
            },
            "section_one": {
                "morning_water_level": 417,
                "water_level_trend": 2,
                "water_level_20h_period": 410,
                "water_temperature": None,
                "air_temperature": None,
                "ice_phenomena": [],
                "daily_precipitation": None,
            },
            # there are no empty objects for sections 933, 966 or 988 if they are not present
        }

    def test_parse_with_water_and_air_temperature(self, datetime_mock, organization, manual_hydro_station):
        parser = KN15TelegramParser(
            f"{manual_hydro_station.station_code} 14081 10417 20021 30410 46510=", organization.uuid
        )
        decoded_data = parser.parse()

        assert decoded_data["section_one"]["water_temperature"] == 6.5
        assert decoded_data["section_one"]["air_temperature"] == 10

    def test_parse_with_water_and_air_temperature_for_negative_air_temperature(
        self, datetime_mock, organization, manual_hydro_station
    ):
        parser = KN15TelegramParser(
            f"{manual_hydro_station.station_code} 14081 10417 20021 30410 46560=", organization.uuid
        )
        decoded_data = parser.parse()

        assert decoded_data["section_one"]["water_temperature"] == 6.5
        assert decoded_data["section_one"]["air_temperature"] == -10

    def test_parse_with_ice_phenomena_code_outside_of_range(self, datetime_mock, organization, manual_hydro_station):
        parser = KN15TelegramParser(
            f"{manual_hydro_station.station_code} 14081 10417 20021 30410 52902=", organization.uuid
        )

        with pytest.raises(
            InvalidTokenException,
            match="Invalid ice phenomena code: 29",
        ):
            _ = parser.parse()

    def test_parse_with_ice_phenomena_for_code_requiring_intensity(
        self, datetime_mock, organization, manual_hydro_station
    ):
        parser = KN15TelegramParser(
            f"{manual_hydro_station.station_code} 14081 10417 20021 30410 51211=", organization.uuid
        )

        with pytest.raises(
            InvalidTokenException,
            match="Ice phenomena intensity needs to be between 1 and 10, found: 11",
        ):
            _ = parser.parse()

    def test_parse_with_ice_phenomena_for_code_not_requiring_intensity(
        self, datetime_mock, organization, manual_hydro_station
    ):
        parser = KN15TelegramParser(
            f"{manual_hydro_station.station_code} 14081 10417 20021 30410 52010=", organization.uuid
        )

        with pytest.raises(
            InvalidTokenException,
            match="Invalid ice phenomena format, 5EEEE expected for the given code: 52010",
        ):
            _ = parser.parse()

    def test_parse_with_single_ice_phenomena_value(self, datetime_mock, organization, manual_hydro_station):
        parser = KN15TelegramParser(
            f"{manual_hydro_station.station_code} 14081 10417 20021 30410 52020=", organization.uuid
        )
        decoded_date = parser.parse()

        assert decoded_date["section_one"]["ice_phenomena"] == [{"code": 20, "intensity": None}]

    def test_parse_with_multiple_ice_phenomena_value(self, datetime_mock, organization, manual_hydro_station):
        parser = KN15TelegramParser(
            f"{manual_hydro_station.station_code} 14081 10417 20021 30410 52020 51210 55008 52121=", organization.uuid
        )
        decoded_date = parser.parse()

        assert decoded_date["section_one"]["ice_phenomena"] == [
            {"code": 20, "intensity": None},
            {"code": 12, "intensity": 10},
            {"code": 50, "intensity": 8},
            {"code": 21, "intensity": None},
        ]

    def test_parse_with_daily_precipitation(self, datetime_mock, organization, manual_hydro_station):
        parser = KN15TelegramParser(
            f"{manual_hydro_station.station_code} 14081 10417 20021 30410 00010=", organization.uuid
        )
        decoded_data = parser.parse()
        assert decoded_data["section_one"]["daily_precipitation"]["precipitation"] == 1
        assert decoded_data["section_one"]["daily_precipitation"]["duration_code"] == 0

    def test_parse_with_daily_precipitation_with_decimal(self, datetime_mock, organization, manual_hydro_station):
        parser = KN15TelegramParser(
            f"{manual_hydro_station.station_code} 14081 10417 20021 30410 09912=", organization.uuid
        )
        decoded_data = parser.parse()
        assert decoded_data["section_one"]["daily_precipitation"]["precipitation"] == 0.1
        assert decoded_data["section_one"]["daily_precipitation"]["duration_code"] == 2

    def test_parse_with_daily_precipitation_with_zero_sum(self, datetime_mock, organization, manual_hydro_station):
        parser = KN15TelegramParser(
            f"{manual_hydro_station.station_code} 14081 10417 20021 30410 00000=", organization.uuid
        )

        decoded_data = parser.parse()
        assert decoded_data["section_one"]["daily_precipitation"]["precipitation"] == 0
        assert decoded_data["section_one"]["daily_precipitation"]["duration_code"] == 0

    def test_parse_with_daily_precipitation_with_non_integer_last_character(
        self, datetime_mock, organization, manual_hydro_station
    ):
        parser = KN15TelegramParser(
            f"{manual_hydro_station.station_code} 14081 10417 20021 30410 0000/=", organization.uuid
        )

        decoded_data = parser.parse()
        assert decoded_data["section_one"]["daily_precipitation"]["precipitation"] == 0
        assert decoded_data["section_one"]["daily_precipitation"]["duration_code"] == 0

    def test_parse_without_daily_precipitation(self, datetime_mock, organization, manual_hydro_station):
        parser = KN15TelegramParser(f"{manual_hydro_station.station_code} 14081 10417 20021 30410=", organization.uuid)

        decoded_data = parser.parse()
        assert decoded_data["section_one"]["daily_precipitation"] is None

    def test_parse_with_unexpected_group(self, datetime_mock, organization, manual_hydro_station):
        parser = KN15TelegramParser(
            f"{manual_hydro_station.station_code} 14081 10417 20021 30410 65432 00000=", organization.uuid
        )

        decoded_data = parser.parse()

        # unexpected group before an optional one will cause the optional group to be skipped,
        # in this case, the daily precipitation will be skipped

        assert decoded_data["section_one"] == {
            "morning_water_level": 417,
            "water_level_trend": 2,
            "water_level_20h_period": 410,
            "water_temperature": None,
            "air_temperature": None,
            "ice_phenomena": [],
            "daily_precipitation": None,
        }


class TestKN15TelegramParserSectionThree:
    def test_parse(self, datetime_mock, organization, manual_hydro_station):
        parser = KN15TelegramParser(
            f"{manual_hydro_station.station_code} 14082 10417 20021 30410 00000 93301 10212=", organization.uuid
        )

        decoded_data = parser.parse()

        assert decoded_data["section_three"] == {"water_level": 212}

    def test_parse_with_unsupported_group(self, datetime_mock, organization, manual_hydro_station):
        parser = KN15TelegramParser(
            f"{manual_hydro_station.station_code} 14082 10417 20021 30410 00000 93302 10212=", organization.uuid
        )
        with pytest.raises(
            InvalidTokenException,
            match=re.escape("Expected data from previous day (code 93301), got: 93302"),
        ):
            parser.parse()

    def test_parse_with_additional_groups(self, datetime_mock, organization, manual_hydro_station):
        parser = KN15TelegramParser(
            f"{manual_hydro_station.station_code} 14082 10417 20021 30410 00000 93301 10212 42126=", organization.uuid
        )

        decoded_data = parser.parse()

        assert decoded_data["section_three"] == {"water_level": 212}


class TestKN15TelegramParserSectionSix:
    def test_parse_with_wrong_last_digit_in_section_one_group_two(
        self, datetime_mock, organization, manual_hydro_station
    ):
        with pytest.raises(
            InvalidTokenException,
            match="Found the following token, but group 14081 doesn't end with 2: 96605",
        ):
            _ = KN15TelegramParser(
                f"{manual_hydro_station.station_code} 14081 10417 20021 30410 00000 96605 10212 22126=",
                organization.uuid,
            )

    def test_parse_with_only_mandatory_data(self, datetime_mock, organization_kyrgyz, manual_hydro_station_kyrgyz):
        parser = KN15TelegramParser(
            f"{manual_hydro_station_kyrgyz.station_code} 14082 10417 20021 30410 00000 96604 10212 22126 51310=",
            organization_kyrgyz.uuid,
        )

        decoded_data = parser.parse()
        assert decoded_data["section_six"] == [
            {
                "water_level": 212,
                "discharge": 12.6,
                "cross_section_area": None,
                "maximum_depth": None,
                "date": "2024-04-13T10:00:00+06:00",
            }
        ]

    def test_parse_with_optional_data(self, datetime_mock, organization_kyrgyz, manual_hydro_station_kyrgyz):
        parser = KN15TelegramParser(
            f"{manual_hydro_station_kyrgyz.station_code} 14082 10417 20021 30410 00000 96604 15212 21126 32133 40020 51310=",
            organization_kyrgyz.uuid,
        )

        decoded_data = parser.parse()
        assert decoded_data["section_six"] == [
            {
                "water_level": -212,
                "discharge": 1.26,
                "cross_section_area": 13.3,
                "maximum_depth": 20,
                "date": "2024-04-13T10:00:00+06:00",
            }
        ]

    def test_parse_with_multiple_966_sections(self, datetime_mock, organization_kyrgyz, manual_hydro_station_kyrgyz):
        parser = KN15TelegramParser(
            f"{manual_hydro_station_kyrgyz.station_code} 14082 10417 20021 30410 00000 "
            f"96604 10212 22126 51310 96604 10250 22130 32133 40040 51410=",
            organization_kyrgyz.uuid,
        )

        decoded_data = parser.parse()
        assert decoded_data["section_six"] == [
            {
                "water_level": 212,
                "discharge": 12.6,
                "cross_section_area": None,
                "maximum_depth": None,
                "date": "2024-04-13T10:00:00+06:00",
            },
            {
                "water_level": 250,
                "discharge": 13.0,
                "cross_section_area": 13.3,
                "maximum_depth": 40,
                "date": "2024-04-14T10:00:00+06:00",
            },
        ]

    def test_parse_with_previous_year_data(self, datetime_mock, organization_kyrgyz, manual_hydro_station_kyrgyz):
        parser = KN15TelegramParser(
            f"{manual_hydro_station_kyrgyz.station_code} 14082 10417 20021 30410 00000 96604 10212 22126 51610=",
            organization_kyrgyz.uuid,
        )

        decoded_data = parser.parse()
        assert decoded_data["section_six"] == [
            {
                "water_level": 212,
                "discharge": 12.6,
                "cross_section_area": None,
                "maximum_depth": None,
                "date": "2023-04-16T10:00:00+06:00",
            }
        ]

    def test_parse_with_additional_sections(self, datetime_mock, organization_kyrgyz, manual_hydro_station_kyrgyz):
        parser = KN15TelegramParser(
            f"{manual_hydro_station_kyrgyz.station_code} 14082 10417 20021 30410 00000 96604 10212 22126 51410 61000=",
            organization_kyrgyz.uuid,
        )

        decoded_data = parser.parse()
        assert decoded_data["section_six"] == [
            {
                "water_level": 212,
                "discharge": 12.6,
                "cross_section_area": None,
                "maximum_depth": None,
                "date": "2024-04-14T10:00:00+06:00",
            }
        ]


class TestKN15TelegramParserSectionEight:
    def test_parse(self, datetime_mock, organization, manual_hydro_station, manual_meteo_station):
        parser = KN15TelegramParser(
            f"{manual_hydro_station.station_code} 14082 10417 20021 30410 00000 98803 111// 21238 30123=",
            organization.uuid,
        )

        decoded_data = parser.parse()
        assert decoded_data["section_eight"] == {
            "decade": 1,
            "timestamp": "2024-03-05T12:00:00+00:00",
            "precipitation": 123,
            "temperature": 12.3,
        }

    def test_parse_when_meteo_station_doesnt_exist(self, datetime_mock, organization, manual_hydro_station):
        parser = KN15TelegramParser(
            f"{manual_hydro_station.station_code} 14082 10417 20021 30410 00000 98803 111// 21238 30123=",
            organization.uuid,
        )

        with pytest.raises(
            MissingMeteoStationException, match="No meteo station with code 12345, but found token: 98803"
        ):
            parser.parse()

    def test_parse_for_entire_month(self, datetime_mock, organization, manual_hydro_station, manual_meteo_station):
        parser = KN15TelegramParser(
            f"{manual_hydro_station.station_code} 14082 10417 20021 30410 00000 98803 130// 21238 30123=",
            organization.uuid,
        )

        decoded_data = parser.parse()
        assert decoded_data["section_eight"] == {
            "decade": 4,
            "timestamp": "2024-03-15T12:00:00+00:00",
            "precipitation": 123,
            "temperature": 12.3,
        }

    def test_parse_for_invalid_decade_identifier(
        self, datetime_mock, organization, manual_hydro_station, manual_meteo_station
    ):
        parser = KN15TelegramParser(
            f"{manual_hydro_station.station_code} 14082 10417 20021 30410 00000 98803 140// 21238 30123=",
            organization.uuid,
        )
        with pytest.raises(
            InvalidTokenException,
            match="Invalid decade identifier, supported identifiers are '11', '22', '33' and '30': 140//",
        ):
            parser.parse()

    def test_parse_for_invalid_precipitation_checksum(
        self, datetime_mock, organization, manual_hydro_station, manual_meteo_station
    ):
        parser = KN15TelegramParser(
            f"{manual_hydro_station.station_code} 14082 10417 20021 30410 00000 98803 111// 21230 30123=",
            organization.uuid,
        )
        with pytest.raises(
            InvalidTokenException,
            match="Check digit sum does not match: 21230",
        ):
            parser.parse()

    def test_parse_for_invalid_temperature_sign(
        self, datetime_mock, organization, manual_hydro_station, manual_meteo_station
    ):
        parser = KN15TelegramParser(
            f"{manual_hydro_station.station_code} 14082 10417 20021 30410 00000 98803 111// 21238 32123=",
            organization.uuid,
        )
        with pytest.raises(
            InvalidTokenException,
            match="Invalid second digit, expected '0' or '1': 32123",
        ):
            parser.parse()

    def test_parse_for_negative_temperature(
        self, datetime_mock, organization, manual_hydro_station, manual_meteo_station
    ):
        parser = KN15TelegramParser(
            f"{manual_hydro_station.station_code} 14082 10417 20021 30410 00000 98803 133// 21238 31023=",
            organization.uuid,
        )
        decoded_data = parser.parse()
        assert decoded_data["section_eight"] == {
            "decade": 3,
            "timestamp": "2024-03-25T12:00:00+00:00",
            "precipitation": 123,
            "temperature": -2.3,
        }

    def test_parse_for_wrong_section_order(
        self, datetime_mock, organization, manual_hydro_station, manual_meteo_station
    ):
        parser = KN15TelegramParser(
            f"{manual_hydro_station.station_code} 14082 10417 20021 30410 00000 98803 21238 133// 31023=",
            organization.uuid,
        )
        with pytest.raises(
            MissingSectionException,
            match="Expected decade section starting with '1', got: 21238",
        ):
            parser.parse()

    def test_parse_for_missing_section(self, datetime_mock, organization, manual_hydro_station, manual_meteo_station):
        parser = KN15TelegramParser(
            f"{manual_hydro_station.station_code} 14082 10417 20021 30410 00000 98803 133// 31023=", organization.uuid
        )
        with pytest.raises(
            MissingSectionException,
            match="Expected precipitation section starting with '2', got: 31023",
        ):
            parser.parse()

    def test_parse_with_additional_groups(
        self, datetime_mock, organization, manual_hydro_station, manual_meteo_station
    ):
        parser = KN15TelegramParser(
            f"{manual_hydro_station.station_code} 14082 10417 20021 30410 00000 98803 122// 21238 31023 41126=",
            organization.uuid,
        )

        decoded_data = parser.parse()

        assert decoded_data["section_eight"] == {
            "decade": 2,
            "timestamp": "2024-03-15T12:00:00+00:00",
            "precipitation": 123,
            "temperature": -2.3,
        }
