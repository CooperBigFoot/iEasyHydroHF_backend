from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone



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
    return

def local_evening(dt: datetime) -> datetime:
    return

def local_previous_morning(dt: datetime) -> datetime:
    return

def local_previous_evening(dt: datetime) -> datetime:
    return
