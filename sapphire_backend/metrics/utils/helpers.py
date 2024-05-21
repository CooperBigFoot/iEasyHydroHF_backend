from datetime import datetime, timezone


def calculate_decade_date(ordinal_number: int):
    days_in_decade = [5, 15, 25]
    idx = (ordinal_number - 1) % 3
    month_increment = (ordinal_number - 1) // 3

    month = month_increment + 1
    day = days_in_decade[idx]

    return datetime(datetime.utcnow().year, month, day, 12, tzinfo=timezone.utc)


def calculate_decade_number(date: datetime) -> int:
    month, day = date.month, date.day

    if 1 <= day <= 10:
        decade = 1
    elif 11 <= day <= 20:
        decade = 2
    elif 21 <= day <= 31:
        decade = 3
    else:
        raise ValueError(f"Day {day} is an invalid day")

    month_decrement = month - 1
    ordinal_number = month_decrement * 3 + decade

    return ordinal_number
