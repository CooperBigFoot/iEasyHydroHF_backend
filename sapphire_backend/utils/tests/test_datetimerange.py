from datetime import datetime, timedelta

import pytest

from sapphire_backend.utils.datetime_helper import DatetimeRange


class TestDatetimeRange:
    def test_datetime_range_valid(self):
        start = datetime(2023, 6, 1)
        end = datetime(2023, 6, 10)
        delta = timedelta(days=1)
        date_range = DatetimeRange(start, end, delta)
        result = list(date_range)
        expected = [
            datetime(2023, 6, 1),
            datetime(2023, 6, 2),
            datetime(2023, 6, 3),
            datetime(2023, 6, 4),
            datetime(2023, 6, 5),
            datetime(2023, 6, 6),
            datetime(2023, 6, 7),
            datetime(2023, 6, 8),
            datetime(2023, 6, 9),
            datetime(2023, 6, 10),
        ]
        assert result == expected

    def test_datetime_range_start_equal_end(self):
        start = datetime(2023, 6, 1)
        end = datetime(2023, 6, 1)
        delta = timedelta(days=1)
        date_range = DatetimeRange(start, end, delta)
        result = list(date_range)
        expected = [datetime(2023, 6, 1)]
        assert result == expected

    def test_datetime_range_end_less_than_start(self):
        start = datetime(2023, 6, 10)
        end = datetime(2023, 6, 1)
        delta = timedelta(days=1)
        with pytest.raises(ValueError, match="End datetime must be greater than or equal to start datetime."):
            DatetimeRange(start, end, delta)

    def test_datetime_range_non_positive_delta(self):
        start = datetime(2023, 6, 1)
        end = datetime(2023, 6, 10)
        delta = timedelta(days=0)
        with pytest.raises(ValueError, match="Delta must be a positive time duration."):
            DatetimeRange(start, end, delta)

        delta = timedelta(days=-1)
        with pytest.raises(ValueError, match="Delta must be a positive time duration."):
            DatetimeRange(start, end, delta)
