from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone
from zoneinfo import ZoneInfo

from sapphire_backend.stations.models import HydrologicalStation, MeteorologicalStation


class SmartDatetime:
    def __init__(self, dt: [str | datetime], station: [HydrologicalStation | MeteorologicalStation], local=True):
        if isinstance(dt, str):
            if local:
                self._dt_utc = datetime.fromisoformat(dt).astimezone(ZoneInfo("UTC"))
            else:
                self._dt_utc = timezone.make_aware(datetime.fromisoformat(dt), timezone=ZoneInfo("UTC"))
        elif isinstance(dt, datetime):
            if local:
                self._dt_utc = dt.astimezone(ZoneInfo("UTC"))
            else:
                if dt.tzinfo is None:
                    self._dt_utc = timezone.make_aware(dt, timezone=ZoneInfo("UTC"))
                else:
                    self._dt_utc = dt
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
        return self.previous_local.astimezone(ZoneInfo("UTC"))

    @property
    def morning_local(self):
        return self.local.replace(hour=8, minute=0, second=0)

    @property
    def morning_utc(self):
        return self.morning_local.astimezone(ZoneInfo("UTC"))

    @property
    def previous_morning_local(self):
        return self.previous_local.replace(hour=8, minute=0, second=0)

    @property
    def previous_morning_utc(self):
        return self.previous_morning_local.astimezone(ZoneInfo("UTC"))

    @property
    def evening_local(self):
        return self._dt_local.replace(hour=20, minute=0, second=0)

    @property
    def evening_utc(self):
        return self.evening_local.astimezone(ZoneInfo("UTC"))

    @property
    def previous_evening_local(self):
        return self.evening_local - timedelta(days=1)

    @property
    def previous_evening_utc(self):
        return self.previous_evening_local.astimezone(ZoneInfo("UTC"))

    @property
    def midday_local(self):
        return self._dt_local.replace(hour=12, minute=0, second=0)

    @property
    def midday_utc(self):
        return self.midday_local.astimezone(ZoneInfo("UTC"))

    @property
    def previous_midday_local(self):
        return self.midday_local - timedelta(days=1)

    @property
    def previous_midday_utc(self):
        return self.previous_midday_local.astimezone(ZoneInfo("UTC"))

    @property
    def day_beginning_local(self):
        return self.morning_local.replace(hour=0, minute=0, second=0)

    @property
    def day_beginning_utc(self):
        return self.day_beginning_local.astimezone(ZoneInfo("UTC"))
