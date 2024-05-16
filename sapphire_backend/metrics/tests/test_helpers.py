from datetime import datetime as dt

from zoneinfo import ZoneInfo

from sapphire_backend.metrics.utils.helpers import calculate_decade_date, calculate_decade_number


class TestMetricsHelpers:
    utc = ZoneInfo("UTC")

    def test_calculate_decade_date(self):
        assert calculate_decade_date(1) == dt(dt.now().year, 1, 5, 12, tzinfo=self.utc)
        assert calculate_decade_date(2) == dt(dt.now().year, 1, 15, 12, tzinfo=self.utc)
        assert calculate_decade_date(3) == dt(dt.now().year, 1, 25, 12, tzinfo=self.utc)
        assert calculate_decade_date(4) == dt(dt.now().year, 2, 5, 12, tzinfo=self.utc)
        assert calculate_decade_date(10) == dt(dt.now().year, 4, 5, 12, tzinfo=self.utc)
        assert calculate_decade_date(36) == dt(dt.now().year, 12, 25, 12, tzinfo=self.utc)

    def test_calculate_decade_number(self):
        assert calculate_decade_number(dt(2000, 1, 1, 12, tzinfo=self.utc)) == 1
        assert calculate_decade_number(dt(2000, 1, 10, 12, tzinfo=self.utc)) == 1
        assert calculate_decade_number(dt(2000, 1, 17, 12, tzinfo=self.utc)) == 2
        assert calculate_decade_number(dt(2000, 1, 24, 12, tzinfo=self.utc)) == 3
        assert calculate_decade_number(dt(2000, 1, 31, 12, tzinfo=self.utc)) == 3
        assert calculate_decade_number(dt(2000, 2, 10, 12, tzinfo=self.utc)) == 4
        assert calculate_decade_number(dt(2000, 2, 11, 12, tzinfo=self.utc)) == 5
        assert calculate_decade_number(dt(2000, 12, 18, 12, tzinfo=self.utc)) == 35
        assert calculate_decade_number(dt(2000, 12, 21, 12, tzinfo=self.utc)) == 36
        assert calculate_decade_number(dt(2000, 12, 25, 12, tzinfo=self.utc)) == 36
