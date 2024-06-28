import re
from datetime import date, datetime

import pytest
from zoneinfo import ZoneInfo

from sapphire_backend.utils.datetime_helper import SmartDatetime


class TestSmartDatetimeModel:
    def test_local_date_str_to_smartdatetime(self, manual_hydro_station_kyrgyz):
        # Test how for a given date string object and tz_included=False,
        # SmartDatetime returns local time with faked UTC timezone
        # and .tz returns a proper datetime object with real timestamp and timezone
        local_date_str = "2024-01-01"
        smart_dt = SmartDatetime(dt=local_date_str, station=manual_hydro_station_kyrgyz, tz_included=False)
        tz_local = manual_hydro_station_kyrgyz.site.timezone

        assert smart_dt.local == datetime(2024, 1, 1, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
        assert smart_dt.tz == datetime(2024, 1, 1, 0, 0, 0, tzinfo=tz_local)

    def test_utc_date_str_to_smartdatetime(self, manual_hydro_station_kyrgyz):
        # Test how for a given date string object, SmartDatetime enforces UTC midnight datetime() when tz_included=True
        utc_date_str = "2024-01-01"
        tz_local = manual_hydro_station_kyrgyz.site.timezone
        smart_dt = SmartDatetime(dt=utc_date_str, station=manual_hydro_station_kyrgyz, tz_included=True)

        assert smart_dt.tz == datetime(2024, 1, 1, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
        assert smart_dt.local == datetime(2024, 1, 1, 0, 0, 0, tzinfo=ZoneInfo("UTC")).astimezone(tz_local).replace(
            tzinfo=ZoneInfo("UTC")
        )

    def test_local_datetime_isostr_to_smartdatetime(self, manual_hydro_station_kyrgyz):
        # Test how for a given ISO datetime string object and tz_included=False,
        # SmartDatetime returns local time with faked UTC timezone
        # and .tz returns a proper datetime object with real timestamp and station's timezone
        # (not the timezone from local_date_str)
        datetime_isostring = "2024-01-01T00:00:00+04:00"
        smart_dt = SmartDatetime(dt=datetime_isostring, station=manual_hydro_station_kyrgyz, tz_included=False)
        tz_local = manual_hydro_station_kyrgyz.site.timezone

        assert smart_dt.local == datetime(2024, 1, 1, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
        assert smart_dt.tz == datetime(2024, 1, 1, 0, 0, 0, tzinfo=tz_local)

    def test_date_obj_to_smartdatetime(self, manual_hydro_station_kyrgyz):
        # Test how for a given date object and tz_included=False,
        # SmartDatetime returns local time with faked UTC timezone (at the day beginning)
        # and .tz returns a proper datetime object with real timestamp and timezone
        date_obj = date(2024, 1, 1)
        smart_dt = SmartDatetime(dt=date_obj, station=manual_hydro_station_kyrgyz, tz_included=False)
        tz_local = manual_hydro_station_kyrgyz.site.timezone

        assert smart_dt.local == datetime(2024, 1, 1, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
        assert smart_dt.tz == datetime(2024, 1, 1, 0, 0, 0, tzinfo=tz_local)

    def test_date_obj_tz_included_to_smartdatetime(self, manual_hydro_station_kyrgyz):
        # Test how for a given date string object and tz_included=True,
        # SmartDatetime raises ValueError because it is not supported, a date obj can't have timezone
        date_obj = date(2024, 1, 1)
        with pytest.raises(
            ValueError,
            match=re.escape(
                "Passing date() to SmartDatetime does not include a timezone, so tz_included must be False"
            ),
        ):
            SmartDatetime(dt=date_obj, station=manual_hydro_station_kyrgyz, tz_included=True)

    def test_datetime_isostr_to_smartdatetime(self, manual_hydro_station_kyrgyz):
        # Test how for a given ISO datetime string object, SmartDatetime uses the timezone of the string
        # (could differ from the station's timezone)
        # when tz_included=True
        datetime_isostring = "2024-01-01T00:00:00+04:00"
        tz_local = manual_hydro_station_kyrgyz.site.timezone
        smart_dt = SmartDatetime(dt=datetime_isostring, station=manual_hydro_station_kyrgyz, tz_included=True)

        assert smart_dt.tz == datetime.fromisoformat(datetime_isostring)
        assert smart_dt.local == datetime.fromisoformat(datetime_isostring).astimezone(tz_local).replace(
            tzinfo=ZoneInfo("UTC")
        )

    def test_local_datetime_to_smartdatetime(self, manual_hydro_station_kyrgyz):
        # Test how for a given datetime object and tz_included = False, SmartDatetime dismisses tzinfo
        # and enforces station's timezone
        tz_local = manual_hydro_station_kyrgyz.site.timezone

        random_tz = ZoneInfo("Asia/Tokyo")
        dt_random_tz = datetime(2024, 1, 1, 15, 0, 0, tzinfo=random_tz)

        smart_dt = SmartDatetime(dt=dt_random_tz, station=manual_hydro_station_kyrgyz, tz_included=False)

        assert smart_dt.tz == datetime(2024, 1, 1, 15, 0, 0, tzinfo=tz_local)
        assert smart_dt.local == datetime(2024, 1, 1, 15, 0, 0, tzinfo=ZoneInfo("UTC"))

    def test_local_date_str(self, manual_hydro_station_kyrgyz):
        local_date_str = "2024-01-01"
        smart_dt = SmartDatetime(dt=local_date_str, station=manual_hydro_station_kyrgyz, tz_included=False)
        tz_local = manual_hydro_station_kyrgyz.site.timezone

        assert smart_dt.local == datetime(2024, 1, 1, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
        assert smart_dt.day_beginning_local == datetime(2024, 1, 1, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
        assert smart_dt.morning_local == datetime(2024, 1, 1, 8, 0, 0, tzinfo=ZoneInfo("UTC"))
        assert smart_dt.midday_local == datetime(2024, 1, 1, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
        assert smart_dt.evening_local == datetime(2024, 1, 1, 20, 0, 0, tzinfo=ZoneInfo("UTC"))

        assert smart_dt.tz == datetime(2024, 1, 1, 0, 0, 0, tzinfo=tz_local)
        assert smart_dt.day_beginning_tz == datetime(2024, 1, 1, 0, 0, 0, tzinfo=tz_local)
        assert smart_dt.morning_tz == datetime(2024, 1, 1, 8, 0, 0, tzinfo=tz_local)
        assert smart_dt.midday_tz == datetime(2024, 1, 1, 12, 0, 0, tzinfo=tz_local)
        assert smart_dt.evening_tz == datetime(2024, 1, 1, 20, 0, 0, tzinfo=tz_local)

    def test_local_date_str_previous_day(self, manual_hydro_station_kyrgyz):
        local_date_str = "2024-01-01"
        smart_dt = SmartDatetime(dt=local_date_str, station=manual_hydro_station_kyrgyz, tz_included=False)
        tz_local = manual_hydro_station_kyrgyz.site.timezone

        assert smart_dt.previous_local == datetime(2023, 12, 31, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
        assert smart_dt.previous_morning_local == datetime(2023, 12, 31, 8, 0, 0, tzinfo=ZoneInfo("UTC"))
        assert smart_dt.previous_midday_local == datetime(2023, 12, 31, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
        assert smart_dt.previous_evening_local == datetime(2023, 12, 31, 20, 0, 0, tzinfo=ZoneInfo("UTC"))

        assert smart_dt.previous_tz == datetime(2023, 12, 31, 0, 0, 0, tzinfo=tz_local)
        assert smart_dt.previous_morning_tz == datetime(2023, 12, 31, 8, 0, 0, tzinfo=tz_local)
        assert smart_dt.previous_midday_tz == datetime(2023, 12, 31, 12, 0, 0, tzinfo=tz_local)
        assert smart_dt.previous_evening_tz == datetime(2023, 12, 31, 20, 0, 0, tzinfo=tz_local)

    def test_local_datetime_to_smartdatetime_current_day(self, manual_hydro_station_kyrgyz):
        tz_local = manual_hydro_station_kyrgyz.site.timezone

        local_dt = datetime(2024, 1, 1, 15, 10, 5, 123, tzinfo=tz_local)
        smart_dt = SmartDatetime(dt=local_dt, station=manual_hydro_station_kyrgyz, tz_included=False)

        assert smart_dt.local == datetime(2024, 1, 1, 15, 10, 5, 123, tzinfo=ZoneInfo("UTC"))
        assert smart_dt.day_beginning_local == datetime(2024, 1, 1, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
        assert smart_dt.morning_local == datetime(2024, 1, 1, 8, 0, 0, tzinfo=ZoneInfo("UTC"))
        assert smart_dt.midday_local == datetime(2024, 1, 1, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
        assert smart_dt.evening_local == datetime(2024, 1, 1, 20, 0, 0, tzinfo=ZoneInfo("UTC"))

        assert smart_dt.tz == datetime(2024, 1, 1, 15, 10, 5, 123, tzinfo=tz_local)
        assert smart_dt.day_beginning_tz == datetime(2024, 1, 1, 0, 0, 0, tzinfo=tz_local)
        assert smart_dt.day_beginning_tz == datetime(2024, 1, 1, 0, 0, 0, tzinfo=tz_local)
        assert smart_dt.morning_tz == datetime(2024, 1, 1, 8, 0, 0, tzinfo=tz_local)
        assert smart_dt.midday_tz == datetime(2024, 1, 1, 12, 0, 0, tzinfo=tz_local)
        assert smart_dt.evening_tz == datetime(2024, 1, 1, 20, 0, 0, tzinfo=tz_local)

    def test_local_datetime_to_smartdatetime_previous_day(self, manual_hydro_station_kyrgyz):
        tz_local = manual_hydro_station_kyrgyz.site.timezone

        local_dt = datetime(2024, 1, 1, 15, 10, 5, 123, tzinfo=tz_local)
        smart_dt = SmartDatetime(dt=local_dt, station=manual_hydro_station_kyrgyz, tz_included=False)

        assert smart_dt.previous_local == datetime(2023, 12, 31, 15, 10, 5, 123, tzinfo=ZoneInfo("UTC"))
        assert smart_dt.previous_morning_local == datetime(2023, 12, 31, 8, 0, 0, tzinfo=ZoneInfo("UTC"))
        assert smart_dt.previous_midday_local == datetime(2023, 12, 31, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
        assert smart_dt.previous_evening_local == datetime(2023, 12, 31, 20, 0, 0, tzinfo=ZoneInfo("UTC"))

        assert smart_dt.previous_tz == datetime(2023, 12, 31, 15, 10, 5, 123, tzinfo=tz_local)
        assert smart_dt.previous_morning_tz == datetime(2023, 12, 31, 8, 0, 0, tzinfo=tz_local)
        assert smart_dt.previous_midday_tz == datetime(2023, 12, 31, 12, 0, 0, tzinfo=tz_local)
        assert smart_dt.previous_evening_tz == datetime(2023, 12, 31, 20, 0, 0, tzinfo=tz_local)
