from datetime import datetime, timedelta

from django.db import connection


def refresh_continuous_aggregate(start_date: str = None, end_date: str = None):
    if None in [start_date, end_date]:  # full refresh
        start_date = "2010-01-01"
        end_date = (datetime.now() + timedelta(days=1)).date().isoformat()
    else:
        # in order to include the end_date
        end_date = (datetime.fromisoformat(end_date) + timedelta(days=1)).date().isoformat()
    with connection.cursor() as cursor:
        cursor.execute(
            f"CALL refresh_continuous_aggregate('public.estimations_water_level_daily_average', '{start_date}', '{end_date}')"
        )
