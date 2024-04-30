import datetime
from unittest.mock import patch

import pytest
from zoneinfo import ZoneInfo

from sapphire_backend.telegrams.exceptions import InvalidTokenException, MissingSectionException
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


class TestKN15TelegramParserSectionZero:
    def test_parse_with_invalid_station_code(self, organization):
        parser = KN15TelegramParser("abcde 29081 10417 20021 30410=", organization.uuid)

        with pytest.raises(InvalidTokenException, match="Invalid station code: abcde"):
            parser.parse()

        parser = KN15TelegramParser("123456 29081 10417 20021 30410=", organization.uuid)

        with pytest.raises(InvalidTokenException, match="Invalid station code: 123456"):
            parser.parse()

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
    def test_parse_for_invalid_date_rollback_invalid_day(self, mock_datetime, organization, manual_hydro_station):
        # April has 30 days
        mock_datetime.now.return_value = datetime.datetime(2024, 4, 30, tzinfo=ZoneInfo("UTC"))
        mock_datetime.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)

        # 31081 means day 31 which is invalid for April
        parser = KN15TelegramParser(f"{manual_hydro_station.station_code} 31081 10417 20021 30410=", organization.uuid)
        decoded_values = parser.parse()
        assert decoded_values["section_zero"]["date"] == "2024-03-31T08:00:00+00:00"

    @patch("sapphire_backend.telegrams.parser.dt")
    def test_parse_for_future_date_rollback_with_day_shift(self, mock_datetime, organization, manual_hydro_station):
        # May has 31 days
        mock_datetime.now.return_value = datetime.datetime(2024, 5, 30, tzinfo=ZoneInfo("UTC"))
        mock_datetime.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)

        # 31081 means day 31 which is a day in the future since the mocked today is the 30th,
        # so we assume the date should be in the previous month
        # and since April doesn't have 31 days, we shift the day for 1 as well
        parser = KN15TelegramParser(f"{manual_hydro_station.station_code} 31081 10417 20021 30410=", organization.uuid)
        decoded_values = parser.parse()
        assert decoded_values["section_zero"]["date"] == "2024-04-30T08:00:00+00:00"

    @patch("sapphire_backend.telegrams.parser.dt")
    def test_parse_for_future_date_rollback_without_day_shift(self, mock_datetime, organization, manual_hydro_station):
        # April has 30 days
        mock_datetime.now.return_value = datetime.datetime(2024, 4, 20, tzinfo=ZoneInfo("UTC"))
        mock_datetime.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)

        # 25081 means day 25 which is a day in the future since the mocked today is the 20th,
        # so we assume the date should be in the previous month
        parser = KN15TelegramParser(f"{manual_hydro_station.station_code} 25081 10417 20021 30410=", organization.uuid)
        decoded_values = parser.parse()
        assert decoded_values["section_zero"]["date"] == "2024-03-25T08:00:00+00:00"

    @patch("sapphire_backend.telegrams.parser.dt")
    def test_parse_for_date_new_year_rollback(self, mock_datetime, organization, manual_hydro_station):
        mock_datetime.now.return_value = datetime.datetime(2024, 1, 20, tzinfo=ZoneInfo("UTC"))
        mock_datetime.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)

        parser = KN15TelegramParser(f"{manual_hydro_station.station_code} 25081 10417 20021 30410=", organization.uuid)

        decoded_values = parser.parse()
        assert decoded_values["section_zero"]["date"] == "2023-12-25T08:00:00+00:00"

    @patch("sapphire_backend.telegrams.parser.dt")
    def test_parse_for_date_leap_year_feb(self, mock_datetime, organization, manual_hydro_station):
        mock_datetime.now.return_value = datetime.datetime(2024, 3, 1, tzinfo=ZoneInfo("UTC"))
        mock_datetime.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)

        parser = KN15TelegramParser(f"{manual_hydro_station.station_code} 30081 10417 20021 30410=", organization.uuid)

        decoded_values = parser.parse()
        assert decoded_values["section_zero"]["date"] == "2024-02-29T08:00:00+00:00"

    @patch("sapphire_backend.telegrams.parser.dt")
    def test_parse_for_date_non_leap_year_feb(self, mock_datetime, organization, manual_hydro_station):
        mock_datetime.now.return_value = datetime.datetime(2023, 3, 1, tzinfo=ZoneInfo("UTC"))
        mock_datetime.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)

        parser = KN15TelegramParser(f"{manual_hydro_station.station_code} 30081 10417 20021 30410=", organization.uuid)

        decoded_values = parser.parse()
        assert decoded_values["section_zero"]["date"] == "2023-02-28T08:00:00+00:00"

    @patch("sapphire_backend.telegrams.parser.dt")
    def test_parse_full_output(self, mock_datetime, organization, manual_hydro_station):
        mock_datetime.now.return_value = datetime.datetime(2024, 4, 15, tzinfo=ZoneInfo("UTC"))
        mock_datetime.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)

        parser = KN15TelegramParser(f"{manual_hydro_station.station_code} 14081 10417 20021 30410=", organization.uuid)

        decoded_values = parser.parse()
        assert decoded_values["section_zero"] == {
            "station_code": manual_hydro_station.station_code,
            "station_name": manual_hydro_station.name,
            "date": "2024-04-14T08:00:00+00:00",
            "section_code": 1,
        }


class TestKN15TelegramParserSectionOne:
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
