from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone

from sapphire_backend.stations.models import MeteorologicalStation, HydrologicalStation


class SmartDatetime():
    def __init__(self, dt: [str | datetime], station: [HydrologicalStation | MeteorologicalStation], local=True):
        if isinstance(dt, str):
            if local:
                self._dt_utc = datetime.fromisoformat(dt).astimezone(ZoneInfo('UTC'))
            else:
                self._dt_utc = timezone.make_aware(datetime.fromisoformat(dt), timezone=ZoneInfo('UTC'))
        elif isinstance(dt, datetime):
            if local:
                self._dt_utc = dt.astimezone(ZoneInfo('UTC'))
            else:
                self._dt_utc = timezone.make_aware(dt, timezone=ZoneInfo('UTC'))

        self._local_timezone = station.site.timezone or settings.TIME_ZONE
        self._dt_local = self._dt_utc.astimezone(ZoneInfo(self._local_timezone))

    @property
    def local_timezone(self):
        return self._local_timezone

    @property
    def local(self):
        return self._dt_local

    @property
    def utc(self):
        return self._dt_utc

    @property
    def previous_local(self):
        return self.local - timedelta(days=1)

    @property
    def previous_utc(self):
        return self.previous_local.astimezone(ZoneInfo('UTC'))

    @property
    def morning_local(self):
        return self.local.replace(hour=8, minute=0, second=0)

    @property
    def morning_utc(self):
        return self.morning_local.astimezone(ZoneInfo('UTC'))

    @property
    def previous_morning_local(self):
        return self.previous_local.replace(hour=8, minute=0, second=0)

    @property
    def previous_morning_utc(self):
        return self.previous_morning_local.astimezone(ZoneInfo('UTC'))

    @property
    def evening_local(self):
        return self._dt_local.replace(hour=20, minute=0, second=0)

    @property
    def evening_utc(self):
        return self.evening_local.astimezone(ZoneInfo('UTC'))

    @property
    def previous_evening_local(self):
        return self.evening_local - timedelta(days=1)

    @property
    def previous_evening_utc(self):
        return self.previous_evening_local.astimezone(ZoneInfo('UTC'))

    @property
    def midday_local(self):
        return self._dt_local.replace(hour=12, minute=0, second=0)

    @property
    def midday_utc(self):
        return self.midday_local.astimezone(ZoneInfo('UTC'))

    @property
    def previous_midday_local(self):
        return self.midday_local - timedelta(days=1)

    @property
    def previous_midday_utc(self):
        return self.previous_midday_local.astimezone(ZoneInfo('UTC'))

    @property
    def day_beginning_local(self):
        return self.morning_local.replace(hour=0, minute=0, second=0)

    @property
    def day_beginning_utc(self):
        return self.day_beginning_local.astimezone(ZoneInfo('UTC'))


def to_utc(dt: datetime) -> datetime:
    utc_datetime = dt.astimezone(ZoneInfo('UTC'))
    return utc_datetime


def to_local_tz(dt: datetime) -> datetime:
    local_datetime = dt.astimezone(ZoneInfo(settings.TIME_ZONE))
    return local_datetime


def local_date(dt: datetime) -> datetime.date:
    return dt.date()


def yesterday_date(dt: datetime) -> datetime.date:
    previous_day = dt - timedelta(days=1)
    return previous_day.date()


def yesterday_morning(dt: datetime) -> datetime:
    previous_day = dt - timedelta(days=1)
    # Set the time to 08:00 AM
    result_datetime = previous_day.replace(hour=8, minute=0, second=0)
    return result_datetime


def local_morning(dt: datetime) -> datetime:
    return dt.replace(hour=8, minute=0, second=0)


def local_evening(dt: datetime) -> datetime:
    return dt.replace(hour=20, minute=0, second=0)


def local_midday(dt: datetime) -> datetime:
    return dt.replace(hour=12, minute=0, second=0)
