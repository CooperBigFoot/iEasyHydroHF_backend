from datetime import date, timedelta

import pytest

from sapphire_backend.utils.datetime_helper import DateRange


class TestDateRange:
    def test_date_range_valid(self):
        start = date(2023, 6, 1)
        end = date(2023, 6, 10)
        delta = timedelta(days=1)
        date_range = DateRange(start, end, delta)
        result = list(date_range)
        expected = [
            date(2023, 6, 1),
            date(2023, 6, 2),
            date(2023, 6, 3),
            date(2023, 6, 4),
            date(2023, 6, 5),
            date(2023, 6, 6),
            date(2023, 6, 7),
            date(2023, 6, 8),
            date(2023, 6, 9),
            date(2023, 6, 10),
        ]
        assert result == expected

    def test_end_date_less_than_start_date(self):
        start = date(2024, 6, 10)
        end = date(2024, 6, 1)
        delta = timedelta(days=1)

        with pytest.raises(ValueError, match="End date must be greater than or equal to start date."):
            DateRange(start=start, end=end, delta=delta)

    def test_zero_day_delta(self):
        start = date(2024, 6, 1)
        end = date(2024, 6, 10)
        delta = timedelta(days=0)

        with pytest.raises(ValueError, match="Delta must be a positive number of days."):
            DateRange(start=start, end=end, delta=delta)

    def test_negative_day_delta(self):
        start = date(2024, 6, 1)
        end = date(2024, 6, 10)
        delta = timedelta(days=-1)

        with pytest.raises(ValueError, match="Delta must be a positive number of days."):
            DateRange(start=start, end=end, delta=delta)

    def test_non_day_delta(self):
        start = date(2024, 6, 1)
        end = date(2024, 6, 10)
        delta = timedelta(hours=12)

        with pytest.raises(ValueError, match="Delta must be specified in whole days."):
            DateRange(start=start, end=end, delta=delta)

    def test_one_day_delta(self):
        start = date(2024, 6, 1)
        end = date(2024, 6, 1)
        delta = timedelta(days=1)

        date_range = DateRange(start=start, end=end, delta=delta)

        expected_dates = [date(2024, 6, 1)]
        generated_dates = list(date_range)

        assert generated_dates == expected_dates
