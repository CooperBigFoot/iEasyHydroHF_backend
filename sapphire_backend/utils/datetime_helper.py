from datetime import date, datetime, timedelta

from zoneinfo import ZoneInfo

from sapphire_backend.stations.models import HydrologicalStation, MeteorologicalStation


class SmartDatetime:
    def __init__(
        self, dt: [str | datetime | date], station: [HydrologicalStation | MeteorologicalStation], tz_included=False
    ):
        self._local_timezone = station.timezone
        if isinstance(dt, str):
            if tz_included:
                dt_tz = datetime.fromisoformat(dt)
                if dt_tz.tzinfo is None:
                    dt_tz = dt_tz.replace(tzinfo=ZoneInfo("UTC"))
                self._dt_tz = dt_tz
            else:
                self._dt_tz = datetime.fromisoformat(dt).replace(tzinfo=self._local_timezone)
        elif isinstance(dt, datetime):
            if tz_included:
                dt_tz = dt
                if dt.tzinfo is None:
                    dt_tz = dt_tz.replace(tzinfo=ZoneInfo("UTC"))
                self._dt_tz = dt_tz
            else:
                self._dt_tz = dt.replace(tzinfo=self._local_timezone)
        elif isinstance(dt, date):
            if tz_included:
                raise ValueError(
                    "Passing date() to SmartDatetime does not include a timezone, so tz_included must be False"
                )
            self._dt_tz = datetime.combine(dt, datetime.min.time()).replace(tzinfo=self._local_timezone)

    @property
    def local_timezone(self):
        return self._local_timezone

    @property
    def tz(self):
        return self._dt_tz.astimezone(self.local_timezone)

    @property
    def day_beginning_tz(self):
        return self.tz.replace(hour=0, minute=0, second=0, microsecond=0)

    @property
    def morning_tz(self):
        return self.tz.replace(hour=8, minute=0, second=0, microsecond=0)

    @property
    def midday_tz(self):
        return self.tz.replace(hour=12, minute=0, second=0, microsecond=0)

    @property
    def evening_tz(self):
        return self.tz.replace(hour=20, minute=0, second=0, microsecond=0)

    @property
    def previous_tz(self):
        return self.tz - timedelta(days=1)

    @property
    def previous_morning_tz(self):
        return self.morning_tz - timedelta(days=1)

    @property
    def previous_midday_tz(self):
        return self.midday_tz - timedelta(days=1)

    @property
    def previous_evening_tz(self):
        return self.evening_tz - timedelta(days=1)

    @property
    def local(self):
        return self.tz.astimezone(self.local_timezone).replace(tzinfo=ZoneInfo("UTC"))

    @property
    def day_beginning_local(self):
        return self.local.replace(hour=0, minute=0, second=0, microsecond=0)

    @property
    def morning_local(self):
        return self.local.replace(hour=8, minute=0, second=0, microsecond=0)

    @property
    def midday_local(self):
        return self.local.replace(hour=12, minute=0, second=0, microsecond=0)

    @property
    def evening_local(self):
        return self.local.replace(hour=20, minute=0, second=0, microsecond=0)

    @property
    def previous_local(self):
        return self.local - timedelta(days=1)

    @property
    def previous_morning_local(self):
        return self.morning_local - timedelta(days=1)

    @property
    def previous_midday_local(self):
        return self.midday_local - timedelta(days=1)

    @property
    def previous_evening_local(self):
        return self.evening_local - timedelta(days=1)

    def __str__(self):
        return f"SmartDatetime local {self.local.isoformat()}, with TZ: {self.tz.isoformat()}"


class DateRange:
    """
    Date generator for a date range given start, end and delta params.
    Includes end date. Only allows delta of days.
    """

    def __init__(self, start: date, end: date, delta: timedelta):
        if end < start:
            raise ValueError("End date must be greater than or equal to start date.")

        if delta <= timedelta(days=0):
            raise ValueError("Delta must be a positive number of days.")

        if delta.days < 1 or delta != timedelta(days=delta.days):
            raise ValueError("Delta must be specified in whole days.")

        self.start = start
        self.end = end
        self.delta = delta

    def __iter__(self):
        current = self.start
        while current <= self.end:
            yield current
            current += self.delta
