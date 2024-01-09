# -*- encoding: UTF-8 -*-
import datetime

import pytz

HYDROYEAR_START_MONTH = 10


def current_hydroyear():
    return hydroyear_for_date(datetime.date.today())


def hydroyear_for_date(date_object):
    if date_object.month < 10:
        return date_object.year
    return date_object.year + 1


def hydroyear_start_date(hydroyear, return_datetime=True,
                         utc=True):
    """Retrieve the starting date for a given hydroyear.

    Args:
        hydroyear: The hydroyear for which the starting date is required.
        return_datetime: Indicates whether to return a datetime.datetime object
            or a datetime.date object, defaults to True.
        utc: Indicates whether the returned datetime.datetime object should be
            timezone aware and be set to UTC time.
    Returns:
        The date when the given hydrological year starts.
    """
    the_date = datetime.datetime(hydroyear - 1, 10, 1)
    if return_datetime:
        if utc:
            return the_date.replace(tzinfo=pytz.utc)
    return the_date.date()
