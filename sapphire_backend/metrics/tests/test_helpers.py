from datetime import datetime as dt

import pytest
from zoneinfo import ZoneInfo

from sapphire_backend.metrics.utils.helpers import PentadDecadeHelper


class TestMetricsHelpers:
    utc = ZoneInfo("UTC")

    def test_calculate_decade_date(self):
        assert PentadDecadeHelper.calculate_decade_date(1) == dt(dt.now().year, 1, 5, 12, tzinfo=self.utc)
        assert PentadDecadeHelper.calculate_decade_date(2) == dt(dt.now().year, 1, 15, 12, tzinfo=self.utc)
        assert PentadDecadeHelper.calculate_decade_date(3) == dt(dt.now().year, 1, 25, 12, tzinfo=self.utc)
        assert PentadDecadeHelper.calculate_decade_date(4) == dt(dt.now().year, 2, 5, 12, tzinfo=self.utc)
        assert PentadDecadeHelper.calculate_decade_date(10) == dt(dt.now().year, 4, 5, 12, tzinfo=self.utc)
        assert PentadDecadeHelper.calculate_decade_date(36) == dt(dt.now().year, 12, 25, 12, tzinfo=self.utc)

    def test_calculate_decade_number_for_date(self):
        assert PentadDecadeHelper.calculate_decade_from_the_date_in_year(dt(2000, 1, 1, 12, tzinfo=self.utc)) == 1
        assert PentadDecadeHelper.calculate_decade_from_the_date_in_year(dt(2000, 1, 10, 12, tzinfo=self.utc)) == 1
        assert PentadDecadeHelper.calculate_decade_from_the_date_in_year(dt(2000, 1, 17, 12, tzinfo=self.utc)) == 2
        assert PentadDecadeHelper.calculate_decade_from_the_date_in_year(dt(2000, 1, 24, 12, tzinfo=self.utc)) == 3
        assert PentadDecadeHelper.calculate_decade_from_the_date_in_year(dt(2000, 1, 31, 12, tzinfo=self.utc)) == 3
        assert PentadDecadeHelper.calculate_decade_from_the_date_in_year(dt(2000, 2, 10, 12, tzinfo=self.utc)) == 4
        assert PentadDecadeHelper.calculate_decade_from_the_date_in_year(dt(2000, 2, 11, 12, tzinfo=self.utc)) == 5
        assert PentadDecadeHelper.calculate_decade_from_the_date_in_year(dt(2000, 12, 18, 12, tzinfo=self.utc)) == 35
        assert PentadDecadeHelper.calculate_decade_from_the_date_in_year(dt(2000, 12, 21, 12, tzinfo=self.utc)) == 36
        assert PentadDecadeHelper.calculate_decade_from_the_date_in_year(dt(2000, 12, 25, 12, tzinfo=self.utc)) == 36

    def test_calculate_decade_number_in_month(self):
        decade_1_range = range(1, 11)
        decade_2_range = range(11, 21)
        decade_3_range = range(21, 32)
        for day in decade_1_range:
            assert PentadDecadeHelper.calculate_decade_from_the_day_in_month(day) == 1
        for day in decade_2_range:
            assert PentadDecadeHelper.calculate_decade_from_the_day_in_month(day) == 2
        for day in decade_3_range:
            assert PentadDecadeHelper.calculate_decade_from_the_day_in_month(day) == 3
        with pytest.raises(ValueError, match="Day 32 is an invalid day"):
            PentadDecadeHelper.calculate_decade_from_the_day_in_month(32)

    def test_calculate_associated_decade_day(self):
        decade_1_range = range(1, 11)
        decade_2_range = range(11, 21)
        decade_3_range = range(21, 32)
        for day in decade_1_range:
            assert PentadDecadeHelper.calculate_associated_decade_day_for_the_day_in_month(day) == 5
        for day in decade_2_range:
            assert PentadDecadeHelper.calculate_associated_decade_day_for_the_day_in_month(day) == 15
        for day in decade_3_range:
            assert PentadDecadeHelper.calculate_associated_decade_day_for_the_day_in_month(day) == 25
        with pytest.raises(ValueError, match="Day 32 is an invalid day"):
            PentadDecadeHelper.calculate_associated_decade_day_for_the_day_in_month(32)

    def test_calculate_pentad_number_in_month(self):
        pentad_1_range = range(1, 6)
        pentad_2_range = range(6, 11)
        pentad_3_range = range(11, 16)
        pentad_4_range = range(16, 21)
        pentad_5_range = range(21, 26)
        pentad_6_range = range(26, 32)
        for day in pentad_1_range:
            assert PentadDecadeHelper.calculate_pentad_ordinal_number_from_the_day_in_month(day) == 1
        for day in pentad_2_range:
            assert PentadDecadeHelper.calculate_pentad_ordinal_number_from_the_day_in_month(day) == 2
        for day in pentad_3_range:
            assert PentadDecadeHelper.calculate_pentad_ordinal_number_from_the_day_in_month(day) == 3
        for day in pentad_4_range:
            assert PentadDecadeHelper.calculate_pentad_ordinal_number_from_the_day_in_month(day) == 4
        for day in pentad_5_range:
            assert PentadDecadeHelper.calculate_pentad_ordinal_number_from_the_day_in_month(day) == 5
        for day in pentad_6_range:
            assert PentadDecadeHelper.calculate_pentad_ordinal_number_from_the_day_in_month(day) == 6
        with pytest.raises(ValueError, match="Day 32 is an invalid day"):
            PentadDecadeHelper.calculate_pentad_ordinal_number_from_the_day_in_month(32)

    def test_calculate_associated_pentad_day(self):
        pentad_1_range = range(1, 6)
        pentad_2_range = range(6, 11)
        pentad_3_range = range(11, 16)
        pentad_4_range = range(16, 21)
        pentad_5_range = range(21, 26)
        pentad_6_range = range(26, 32)
        for day in pentad_1_range:
            assert PentadDecadeHelper.calculate_associated_pentad_day_from_the_day_int_month(day) == 3
        for day in pentad_2_range:
            assert PentadDecadeHelper.calculate_associated_pentad_day_from_the_day_int_month(day) == 8
        for day in pentad_3_range:
            assert PentadDecadeHelper.calculate_associated_pentad_day_from_the_day_int_month(day) == 13
        for day in pentad_4_range:
            assert PentadDecadeHelper.calculate_associated_pentad_day_from_the_day_int_month(day) == 18
        for day in pentad_5_range:
            assert PentadDecadeHelper.calculate_associated_pentad_day_from_the_day_int_month(day) == 23
        for day in pentad_6_range:
            assert PentadDecadeHelper.calculate_associated_pentad_day_from_the_day_int_month(day) == 28
        with pytest.raises(ValueError, match="Day 32 is an invalid day"):
            PentadDecadeHelper.calculate_associated_pentad_day_from_the_day_int_month(32)

    def test_days_in_pentad(self):
        assert PentadDecadeHelper.days_in_pentad == [5, 10, 15, 20, 25, 30]

    def test_calculate_pentad_ordinal_number(self):
        # Test first month pentads
        assert PentadDecadeHelper.calculate_pentad_from_date(dt(2024, 1, 3)) == 1
        assert PentadDecadeHelper.calculate_pentad_from_date(dt(2024, 1, 8)) == 2
        assert PentadDecadeHelper.calculate_pentad_from_date(dt(2024, 1, 13)) == 3

        # Test mid-year pentads
        assert PentadDecadeHelper.calculate_pentad_from_date(dt(2024, 6, 18)) == 34

        # Test last month pentads
        assert PentadDecadeHelper.calculate_pentad_from_date(dt(2024, 12, 28)) == 72
