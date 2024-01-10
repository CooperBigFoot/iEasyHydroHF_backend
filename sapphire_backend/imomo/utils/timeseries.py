import calendar
import datetime

# import pytz
from datetime import timedelta

from dateutil.relativedelta import relativedelta

from sapphire_backend.imomo import errors


def get_year_decade_from_data(date_time):
    day_to_decade_map = {
        5: 1,
        15: 2,
        25: 3,
    }
    full_month_decades = (date_time.month - 1) * 3

    try:
        current_month_decade = day_to_decade_map[date_time.day]
    except IndexError:
        raise errors.IMomoError("Invalid decade date time")

    return full_month_decades + current_month_decade


def get_month_period(date):
    _, last_day = calendar.monthrange(date.year, date.month)
    return date.replace(day=1), date.replace(day=last_day)


def get_decade_period(date):
    if date.day <= 10:
        return date.replace(day=1), date.replace(day=10)
    elif date.day <= 20:
        return date.replace(day=11), date.replace(day=20)
    else:
        _, last_day = calendar.monthrange(date.year, date.month)
        return date.replace(day=21), date.replace(day=last_day)


def get_fiveday_period(date):
    if date.day <= 5:
        return date.replace(day=1), date.replace(day=5)
    if date.day <= 10:
        return date.replace(day=6), date.replace(day=10)
    if date.day <= 15:
        return date.replace(day=11), date.replace(day=15)
    if date.day <= 20:
        return date.replace(day=16), date.replace(day=20)
    elif date.day <= 25:
        return date.replace(day=21), date.replace(day=26)
    else:
        _, last_day = calendar.monthrange(date.year, date.month)
        return date.replace(day=26), date.replace(day=last_day)


def get_day_in_period_month(date):
    return date.day


def get_day_in_period_decade(date):
    first_day, last_day = get_decade_period(date)
    return date.day - first_day.day + 1


def get_day_in_period_fiveday(date):
    first_day, last_day = get_fiveday_period(date)
    return date.day - first_day.day + 1


def get_period_date(date, frequency):
    date = datetime.date(date.year, date.month, date.day)
    if frequency == "monthly":
        return get_month_period(date)
    if frequency == "decade":
        return get_decade_period(date)
    if frequency == "pentadal":
        return get_fiveday_period(date)


def get_day_in_period(date, frequency):
    date = datetime.date(date.year, date.month, date.day)
    if frequency == "monthly":
        return get_day_in_period_month(date)
    if frequency == "decade":
        return get_day_in_period_decade(date)
    if frequency == "pentadal":
        return get_day_in_period_fiveday(date)


def get_issue_date(first_day, last_day, issue_date_offset, frequency):
    last_day_day_in_period = get_day_in_period(last_day, frequency)
    offset = min(issue_date_offset, last_day_day_in_period - 1)
    return first_day + relativedelta(days=offset)


def get_previous_period_details(date, issue_date_offset, frequency):
    last_day_in_previous_period = last_date_in_previous_period(date, frequency)
    first_day, last_day = get_period_date(last_day_in_previous_period, frequency)
    issue_date = get_issue_date(first_day, last_day, issue_date_offset, frequency)
    return first_day, last_day, issue_date


def last_date_in_previous_period(date, frequency):
    date = datetime.datetime(date.year, date.month, date.day, tzinfo=pytz.utc)
    first_day_, last_day_ = get_period_date(date, frequency)
    return first_day_ - relativedelta(days=1)


def get_current_period_details(date, issue_date_offset, frequency):
    date = datetime.datetime(date.year, date.month, date.day, tzinfo=pytz.utc)
    first_day, last_day = get_period_date(date, frequency)

    issue_date = get_issue_date(first_day, last_day, issue_date_offset, frequency)

    return first_day, last_day, issue_date


def get_next_period_details(date, issue_date_offset, frequency):
    date = datetime.datetime(date.year, date.month, date.day, tzinfo=pytz.utc)
    first_day_, last_day_ = get_period_date(date, frequency)
    first_day_in_next_period = last_day_ + relativedelta(days=1)

    first_day, last_day = get_period_date(first_day_in_next_period, frequency)

    issue_date = get_issue_date(first_day, last_day, issue_date_offset, frequency)

    return first_day, last_day, issue_date


def date_range(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def get_fiveday_interval(date):
    #  Every month there are exactly six 5-day values
    #   (1-5, 6-10, 11-15, 16-20, 21-25, 26-end)
    month_range = calendar.monthrange(date.year, date.month)[1]
    five_day_intervals = [
        (1, 3, 5),
        (6, 8, 10),
        (11, 13, 15),
        (16, 18, 20),
        (21, 23, 25),
        (26, 28, month_range),
    ]

    for interval_start, fiveday_date, interval_end in five_day_intervals:
        if interval_start <= date.day <= interval_end:
            interval_start = date.replace(day=interval_start, hour=12, minute=0, second=0, microsecond=0)

            fiveday_datetime = date.replace(day=fiveday_date, hour=12, minute=0, second=0, microsecond=0)

            interval_end = date.replace(day=interval_end, hour=12, minute=0, second=0, microsecond=0)

            return interval_start, fiveday_datetime, interval_end


def get_fiveday_interval_with_offset(date, offset):
    start, fiveday_datetime, end = get_fiveday_interval(date)
    for x in range(abs(offset)):
        if offset < 0:
            date = start - relativedelta(days=1)
        elif offset > 0:
            date = end + relativedelta(days=1)

        start, fiveday_datetime, end = get_fiveday_interval(date)

    return start, fiveday_datetime, end


def get_fiveday_intervals_for_range(range_start, range_end):
    intervals = []

    start_interval = get_fiveday_datetime(range_start)
    end_interval = get_fiveday_datetime(range_end)

    current_interval = start_interval

    while current_interval < end_interval:
        if current_interval.day == 3:
            current_interval = current_interval.replace(day=8)
        elif current_interval.day == 8:
            current_interval = current_interval.replace(day=13)
        elif current_interval.day == 13:
            current_interval = current_interval.replace(day=18)
        elif current_interval.day == 18:
            current_interval = current_interval.replace(day=23)
        elif current_interval.day == 23:
            current_interval = current_interval.replace(day=28)
        else:
            current_interval = current_interval + relativedelta(months=1)
            current_interval = current_interval.replace(day=3)

        intervals.append(current_interval)

    return intervals


def get_fiveday_datetime(date, offset=0):
    _, five_day_date, _ = get_fiveday_interval_with_offset(date, offset)
    return five_day_date


def get_decade_interval(date):
    if isinstance(date, datetime.date):
        date = datetime.datetime(date.year, date.month, date.day)
    month_range = calendar.monthrange(date.year, date.month)[1]
    decade_intervals = [
        (1, 5, 10),
        (11, 15, 20),
        (21, 25, month_range),
    ]

    for interval_start, decade_date, interval_end in decade_intervals:
        if interval_start <= date.day <= interval_end:
            interval_start = date.replace(day=interval_start, hour=12, minute=0, second=0, microsecond=0)
            decade_datetime = date.replace(day=decade_date, hour=12, minute=0, second=0, microsecond=0)
            interval_end = date.replace(day=interval_end, hour=12, minute=0, second=0, microsecond=0)

            return interval_start, decade_datetime, interval_end


def get_decade_interval_with_offset(date, offset):
    start, decade_datetime, end = get_decade_interval(date)
    for x in range(abs(offset)):
        if offset < 0:
            date = start - relativedelta(days=1)
        elif offset > 0:
            date = end + relativedelta(days=1)

        start, decade_datetime, end = get_decade_interval(date)

    return start, decade_datetime, end


def get_decade_datetime(date, offset=0):
    _, decade_date, _ = get_decade_interval_with_offset(date, offset)
    return decade_date


def get_decade_intervals_for_range(range_start, range_end):
    intervals = []

    start_interval = get_decade_datetime(range_start)
    end_interval = get_decade_datetime(range_end)

    current_interval = start_interval
    intervals.append(current_interval)

    while current_interval < end_interval:
        if current_interval.day == 5:
            current_interval = current_interval.replace(day=15)
        elif current_interval.day == 15:
            current_interval = current_interval.replace(day=25)
        else:
            current_interval = current_interval + relativedelta(months=1)
            current_interval = current_interval.replace(day=5)

        intervals.append(current_interval)

    return intervals


def get_decade_from_date(date):
    date_to_decade = {
        5: 1,
        15: 2,
        25: 3,
    }
    return date_to_decade[date]


def get_decade_date_from_params(year, month, decade_in_month):
    decade_to_date = {
        1: 5,
        2: 15,
        3: 25,
    }
    _, date, _ = get_decade_interval(datetime.datetime(year, month, decade_to_date[decade_in_month], tzinfo=pytz.utc))
    return date


def get_month_date_from_params(year, month):
    _, date, _ = get_month_interval(datetime.datetime(year, month, 1, tzinfo=pytz.utc))
    return date


def get_month_interval(date):
    month_range = calendar.monthrange(date.year, date.month)[1]
    interval_start_datetime = date.replace(day=1, hour=12, minute=0, second=0, microsecond=0)
    decade_datetime = date.replace(day=15, hour=12, minute=0, second=0, microsecond=0)
    interval_end_datetime = date.replace(day=month_range, hour=12, minute=0, second=0, microsecond=0)
    return interval_start_datetime, decade_datetime, interval_end_datetime


def to_morning_datetime(date):
    return date.replace(hour=8, minute=0, second=0, microsecond=0, tzinfo=None)


def to_evening_datetime(date):
    return date.replace(hour=20, minute=0, second=0, microsecond=0, tzinfo=None)


def to_daily_average_datetime(date):
    return date.replace(hour=12, minute=0, second=0, microsecond=0, tzinfo=None)
