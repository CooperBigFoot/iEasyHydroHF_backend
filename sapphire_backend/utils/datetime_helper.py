from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings

from sapphire_backend.stations.models import HydrologicalStation, MeteorologicalStation


class SmartDatetimeOLD:
    def __init__(self, dt: [str | datetime], station: [HydrologicalStation | MeteorologicalStation], local=True):
        self._local_timezone = station.site.timezone or ZoneInfo(settings.TIME_ZONE)
        if isinstance(dt, str):
            if local:
                self._dt_utc = (
                    datetime.fromisoformat(dt).replace(tzinfo=self._local_timezone).astimezone(ZoneInfo("UTC"))
                )
            else:
                self._dt_utc = datetime.fromisoformat(dt).replace(tzinfo=ZoneInfo("UTC"))
        elif isinstance(dt, datetime):
            if local:
                self._dt_utc = dt.replace(tzinfo=self._local_timezone).astimezone(ZoneInfo("UTC"))
            else:
                # overwrite any tzinfo and enforce UTC
                self._dt_utc = dt.replace(tzinfo=ZoneInfo("UTC"))
        self._dt_local = self._dt_utc.astimezone(self._local_timezone)

    @property
    def local_timezone(self):
        return self._local_timezone

    @property
    def local(self):
        return self._dt_local

    @property
    def local_faketz(self):
        return self._dt_local.replace(tzinfo=ZoneInfo('UTC'))

    @property
    def utc(self):
        return self._dt_utc

    @property
    def previous_local(self):
        return self.local - timedelta(days=1)

    @property
    def previous_local_faketz(self):
        return self.local_faketz - timedelta(days=1)

    @property
    def previous_utc(self):
        return self.previous_local.astimezone(ZoneInfo("UTC"))

    @property
    def morning_local(self):
        return self.local.replace(hour=8, minute=0, second=0, microsecond=0)

    @property
    def morning_local_faketz(self):
        return self.local.replace(hour=8, minute=0, second=0, microsecond=0, tzinfo=ZoneInfo('UTC'))

    @property
    def morning_utc(self):
        return self.morning_local.astimezone(ZoneInfo("UTC"))

    @property
    def previous_morning_local(self):
        return self.previous_local.replace(hour=8, minute=0, second=0, microsecond=0)

    @property
    def previous_morning_local_faketz(self):
        return self.previous_local.replace(hour=8, minute=0, second=0, microsecond=0, tzinfo=ZoneInfo('UTC'))

    @property
    def previous_morning_utc(self):
        return self.previous_morning_local.astimezone(ZoneInfo("UTC"))

    @property
    def evening_local(self):
        return self._dt_local.replace(hour=20, minute=0, second=0, microsecond=0)

    @property
    def evening_local_faketz(self):
        return self._dt_local.replace(hour=20, minute=0, second=0, microsecond=0, tzinfo=ZoneInfo('UTC'))

    @property
    def evening_utc(self):
        return self.evening_local.astimezone(ZoneInfo("UTC"))

    @property
    def previous_evening_local(self):
        return self.evening_local - timedelta(days=1)

    @property
    def previous_evening_local_faketz(self):
        return self.evening_local_faketz - timedelta(days=1)

    @property
    def previous_evening_utc(self):
        return self.previous_evening_local.astimezone(ZoneInfo("UTC"))

    @property
    def midday_local(self):
        return self._dt_local.replace(hour=12, minute=0, second=0, microsecond=0)

    @property
    def midday_local_faketz(self):
        return self._dt_local.replace(hour=12, minute=0, second=0, microsecond=0, tzinfo=ZoneInfo('UTC'))

    @property
    def midday_utc(self):
        return self.midday_local.astimezone(ZoneInfo("UTC"))

    @property
    def previous_midday_local(self):
        return self.midday_local - timedelta(days=1)

    @property
    def previous_midday_local_faketz(self):
        return self.midday_local_faketz - timedelta(days=1)

    @property
    def previous_midday_utc(self):
        return self.previous_midday_local.astimezone(ZoneInfo("UTC"))

    @property
    def day_beginning_local(self):
        return self.morning_local.replace(hour=0, minute=0, second=0, microsecond=0)

    @property
    def day_beginning_local_faketz(self):
        return self.morning_local.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=ZoneInfo('UTC'))

    @property
    def day_beginning_utc(self):
        return self.day_beginning_local.astimezone(ZoneInfo("UTC"))

    def __str__(self):
        return f"SmartDatetime local {self.local.isoformat()}, UTC {self.utc.isoformat()}"


class SmartDatetime:
    def __init__(self, dt: [str | datetime], station: [HydrologicalStation | MeteorologicalStation], tz_included=False):
        self._local_timezone = station.site.timezone or ZoneInfo(settings.TIME_ZONE)
        if isinstance(dt, str):
            if tz_included:
                dt_tz = datetime.fromisoformat(dt)
                if dt_tz.tzinfo is None:
                    dt_tz = dt_tz.replace(tzinfo=ZoneInfo('UTC'))
                self._dt_tz = dt_tz
            else:
                self._dt_tz = datetime.fromisoformat(dt).replace(tzinfo=self._local_timezone)
        elif isinstance(dt, datetime):
            if tz_included:
                dt_tz = dt
                if dt.tzinfo is None:
                    dt_tz = dt_tz.replace(tzinfo=ZoneInfo('UTC'))
                self._dt_tz = dt_tz
            else:
                self._dt_tz = dt.replace(tzinfo=self._local_timezone)

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
        return self.tz.astimezone(self.local_timezone).replace(tzinfo=ZoneInfo('UTC'))

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
