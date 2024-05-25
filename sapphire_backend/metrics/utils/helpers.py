from datetime import datetime, timezone
from math import ceil

import pandas as pd

from ..choices import HydrologicalMetricName


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


def transform_daily_operational_data(
    data: list[dict[str, float | None]]
) -> dict[str, dict[str, dict[str, float | int]]]:
    df = pd.DataFrame(data)
    if df.empty:
        return {}
    df["timestamp_local"] = pd.to_datetime(df["timestamp_local"])
    df["date"] = df["timestamp_local"].dt.date
    df["time"] = df["timestamp_local"].dt.strftime("%H:%M")

    first_day_of_given_month = df["date"].min()
    last_day_previous_month_data = df[df["date"] == first_day_of_given_month]

    # get the morning water level to be able to calculate the trend
    previous_day_water_level = None
    if not last_day_previous_month_data.empty:
        morning_data = last_day_previous_month_data[last_day_previous_month_data["time"] == "08:00"]
        if not morning_data.empty:
            previous_day_water_level = ceil(
                morning_data[morning_data["metric_name"] == HydrologicalMetricName.WATER_LEVEL_DAILY][
                    "avg_value"
                ].iloc[0]
            )
    # exclude the last day of the previous month
    df = df[df["date"] != first_day_of_given_month]

    results = {}

    for date in df["date"].unique():
        daily_data = df[df["date"] == date]
        day_dict = {
            "morning_data": {},
            "evening_data": {},
            "daily_data": {},
        }

        morning_data = daily_data[daily_data["time"] == "08:00"]
        if not morning_data.empty:
            water_level_morning = morning_data[
                morning_data["metric_name"] == HydrologicalMetricName.WATER_LEVEL_DAILY
            ]["avg_value"]
            water_discharge_morning = morning_data[
                morning_data["metric_name"] == HydrologicalMetricName.WATER_DISCHARGE_DAILY
            ]["avg_value"]
            morning_water_level_value = ceil(water_level_morning.iloc[0]) if not water_level_morning.empty else None
            day_dict["morning_data"][HydrologicalMetricName.WATER_LEVEL_DAILY] = morning_water_level_value
            day_dict["morning_data"][HydrologicalMetricName.WATER_DISCHARGE_DAILY] = (
                round(water_discharge_morning.iloc[0], 1) if not water_discharge_morning.empty else None
            )
            if previous_day_water_level is not None and morning_water_level_value is not None:
                day_dict["morning_data"]["water_level_trend"] = morning_water_level_value - previous_day_water_level

            previous_day_water_level = morning_water_level_value
        else:
            previous_day_water_level = None

        evening_data = daily_data[daily_data["time"] == "20:00"]
        if not evening_data.empty:
            water_level_evening = evening_data[
                evening_data["metric_name"] == HydrologicalMetricName.WATER_LEVEL_DAILY
            ]["avg_value"]
            water_discharge_evening = evening_data[
                evening_data["metric_name"] == HydrologicalMetricName.WATER_DISCHARGE_DAILY
            ]["avg_value"]
            day_dict["evening_data"][HydrologicalMetricName.WATER_LEVEL_DAILY] = (
                ceil(water_level_evening.iloc[0]) if not water_level_evening.empty else None
            )
            day_dict["evening_data"][HydrologicalMetricName.WATER_DISCHARGE_DAILY] = (
                round(water_discharge_evening.iloc[0], 1) if not water_discharge_evening.empty else None
            )

        ice_phenomena_data = daily_data[daily_data["metric_name"] == HydrologicalMetricName.ICE_PHENOMENA_OBSERVATION]
        day_dict["daily_data"][HydrologicalMetricName.ICE_PHENOMENA_OBSERVATION] = ice_phenomena_data[
            ["avg_value", "value_code"]
        ].to_dict("records")

        daily_precipitation_data = daily_data[daily_data["metric_name"] == HydrologicalMetricName.PRECIPITATION_DAILY]
        day_dict["daily_data"][HydrologicalMetricName.PRECIPITATION_DAILY] = (
            daily_precipitation_data[["avg_value", "value_code"]].iloc[0].to_dict()
            if not daily_precipitation_data.empty
            else None
        )

        for metric in [
            HydrologicalMetricName.WATER_TEMPERATURE,
            HydrologicalMetricName.AIR_TEMPERATURE,
            HydrologicalMetricName.WATER_LEVEL_DAILY_AVERAGE,
            HydrologicalMetricName.WATER_DISCHARGE_DAILY_AVERAGE,
        ]:
            metric_data = daily_data[daily_data["metric_name"] == metric]["avg_value"]
            day_dict["daily_data"][metric] = (
                round(
                    metric_data.iloc[0], 1 if metric != HydrologicalMetricName.WATER_LEVEL_DAILY_AVERAGE.value else 0
                )
                if not metric_data.empty
                else None
            )

        results[date.strftime("%Y-%m-%d")] = day_dict

    return results


def transform_discharge_operational_data(data: list[dict[str, float | None]]) -> dict[str, dict[str, float | int]]:
    df = pd.DataFrame(data)
    if df.empty:
        return {}

    df["timestamp_local"] = pd.to_datetime(df["timestamp_local"])
    df["date"] = df["timestamp_local"].dt.date

    results = {}

    for date in df["date"].unique():
        daily_data = df[df["date"] == date]
        water_level = daily_data[daily_data["metric_name"] == HydrologicalMetricName.WATER_LEVEL_DECADAL]["avg_value"]
        water_level_value = ceil(water_level.iloc[0]) if not water_level.empty else None
        water_discharge = daily_data[daily_data["metric_name"] == HydrologicalMetricName.WATER_DISCHARGE_DAILY][
            "avg_value"
        ]
        water_discharge_value = round(water_discharge.iloc[0], 1) if not water_discharge.empty else None
        river_cross_section = daily_data[daily_data["metric_name"] == HydrologicalMetricName.RIVER_CROSS_SECTION_AREA][
            "avg_value"
        ]
        river_cross_section_value = round(river_cross_section.iloc[0], 2) if not river_cross_section.empty else None

        results[date.strftime("%Y-%m-%d")] = {
            HydrologicalMetricName.WATER_LEVEL_DECADAL.value: water_level_value,
            HydrologicalMetricName.WATER_DISCHARGE_DAILY.value: water_discharge_value,
            HydrologicalMetricName.RIVER_CROSS_SECTION_AREA.value: river_cross_section_value,
        }

    return results
