from datetime import datetime, timezone


def calculate_decade_date(ordinal_number: int):
    days_in_decade = [5, 15, 25]
    idx = (ordinal_number - 1) % 3
    month_increment = (ordinal_number - 1) // 3

    month = month_increment + 1
    day = days_in_decade[idx]

    return datetime(datetime.utcnow().year, month, day, 12, tzinfo=timezone.utc)
