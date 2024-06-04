from datetime import datetime, timezone
from math import ceil

import pandas as pd

from sapphire_backend.utils.daily_precipitation_mapper import DailyPrecipitationCodeMapper
from sapphire_backend.utils.ice_phenomena_mapper import IcePhenomenaCodeMapper
from sapphire_backend.utils.rounding import hydrological_round

from ..choices import HydrologicalMetricName


def calculate_decade_date(ordinal_number: int):
    days_in_decade = [5, 15, 25]
    idx = (ordinal_number - 1) % 3
    month_increment = (ordinal_number - 1) // 3

    month = month_increment + 1
    day = days_in_decade[idx]

    return datetime(datetime.utcnow().year, month, day, 12, tzinfo=timezone.utc)


def calculate_date_from_month_and_decade_number(month: int, ordinal_number: int):
    decade_to_day_mapping = {1: 5, 2: 15, 3: 25, 4: 15}
    return datetime(datetime.utcnow().year, month, decade_to_day_mapping[ordinal_number], 12, tzinfo=timezone.utc)


def calculate_decade_from_day_in_month(day: int) -> int:
    if 1 <= day <= 10:
        decade = 1
    elif 11 <= day <= 20:
        decade = 2
    elif 21 <= day <= 31:
        decade = 3
    else:
        raise ValueError(f"Day {day} is an invalid day")

    return decade


def calculate_decade_number(date: datetime) -> int:
    month, day = date.month, date.day

    decade = calculate_decade_from_day_in_month(day)

    month_decrement = month - 1
    ordinal_number = month_decrement * 3 + decade

    return ordinal_number


class OperationalJournalDataTransformer:
    def __init__(self, data: list[dict[str, float | None]]):
        self.original_data = data
        self.df = self._convert_data_to_dataframe()
        self.is_empty = self.df.empty

    def _convert_data_to_dataframe(self):
        df = pd.DataFrame(self.original_data)
        if not df.empty:
            df["timestamp_local"] = pd.to_datetime(df["timestamp_local"])
            df["date"] = df["timestamp_local"].dt.date
            df["time"] = df["timestamp_local"].dt.strftime("%H:%M")

        return df

    @staticmethod
    def _get_morning_data(data: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
        return data[data["time"] == "08:00"]

    @staticmethod
    def _get_evening_data(data: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
        return data[data["time"] == "20:00"]

    @staticmethod
    def _get_metric_value(data: pd.DataFrame | pd.Series, metric: str) -> int | float | str:
        if not data.empty:
            metric_value = data[data["metric_name"] == metric]["avg_value"]
            if metric_value.empty:
                return "--"
            if metric in [
                HydrologicalMetricName.WATER_LEVEL_DAILY,
                HydrologicalMetricName.WATER_LEVEL_DAILY_AVERAGE,
                HydrologicalMetricName.WATER_LEVEL_DECADE_AVERAGE,
            ]:
                return ceil(metric_value.iloc[0])
            elif metric in [
                HydrologicalMetricName.WATER_DISCHARGE_DAILY,
                HydrologicalMetricName.WATER_DISCHARGE_DAILY_AVERAGE,
                HydrologicalMetricName.WATER_DISCHARGE_DECADE_AVERAGE,
            ]:
                return hydrological_round(metric_value.iloc[0])
            else:
                return round(metric_value.iloc[0], 1)

        return "--"

    @staticmethod
    def _get_ice_phenomena(data: pd.DataFrame | pd.Series) -> str:
        output_string = "--"
        if not data.empty:
            ice_phenomena_data = data[data["metric_name"] == HydrologicalMetricName.ICE_PHENOMENA_OBSERVATION]
            values = ice_phenomena_data[["avg_value", "value_code"]].to_dict("records")
            strings = []
            for value in values:
                description = IcePhenomenaCodeMapper(value["value_code"]).get_description()
                intensity = f" ({round(value['avg_value'] * 10, 0)}%)" if value["avg_value"] != -1 else ""
                strings.append(f"{description}{intensity}")
            output_string = ",".join(strings) if strings else "--"

        return output_string

    @staticmethod
    def _get_daily_precipitation(data: pd.DataFrame | pd.Series) -> str:
        output_string = "--"
        if not data.empty:
            daily_precipitation_data = data[data["metric_name"] == HydrologicalMetricName.PRECIPITATION_DAILY]
            if not daily_precipitation_data.empty:
                value = daily_precipitation_data[["avg_value", "value_code"]].iloc[0].to_dict()
                description = DailyPrecipitationCodeMapper(value["value_code"]).get_description()
                output_string = f"{round(value['avg_value'], 1)} ({description})"

        return output_string

    @staticmethod
    def _get_daily_data_extremes(daily_data: list[dict[str, str | float | int]]) -> list[dict[str, str | float]]:
        relevant_metrics = [
            "water_level_morning",
            "water_discharge_morning",
            "water_level_evening",
            "water_discharge_evening",
            "water_level_average",
            "water_discharge_average",
            "water_temperature",
            "air_temperature",
        ]

        min_row = {"id": "min", "date": "minimum"}
        max_row = {"id": "max", "date": "maximum"}

        for metric in relevant_metrics:
            valid_values = [row[metric] for row in daily_data if row[metric] != "--"]
            if valid_values:
                min_row[metric] = min(valid_values)
                max_row[metric] = max(valid_values)
            else:
                min_row[metric] = "--"
                max_row[metric] = "--"

        return [min_row, max_row]

    @staticmethod
    def _get_monthly_averages_from_decadal_data(decadal_data: list[dict[int | str, int | float | str]]):
        avg_row = {"id": "avg", "decade": "average"}
        for metric in ["water_level", "water_discharge"]:
            valid_values = [row[metric] for row in decadal_data if row[metric] != "--"]
            if valid_values:
                avg_value = sum(valid_values) / len(valid_values)
                avg_row[metric] = hydrological_round(avg_value) if metric == "water_discharge" else ceil(avg_value)
            else:
                avg_row[metric] = "--"

        return avg_row

    def get_daily_data(self) -> list[dict[str, str | float | int]]:
        df = self.df
        results = []
        if self.is_empty:
            return results

        previous_month_last_day = df["date"].min()
        previous_month_last_day_data = df[df["date"] == previous_month_last_day]

        # get morning water_level to be able to calculate the trend on the first day of the given month
        previous_day_water_level = None
        if not previous_month_last_day_data.empty:
            morning_data = self._get_morning_data(previous_month_last_day_data)
            previous_day_water_level = self._get_metric_value(morning_data, HydrologicalMetricName.WATER_LEVEL_DAILY)

        # exclude the last day of the previous month from the dataframe
        df = df[df["date"] != previous_month_last_day]

        # iterate over the existing dates
        for date in df["date"].unique():
            daily_data = df[df["date"] == date]
            day_dict = {}

            # get morning data first
            morning_data = self._get_morning_data(daily_data)
            if not morning_data.empty:
                water_level_morning = self._get_metric_value(morning_data, HydrologicalMetricName.WATER_LEVEL_DAILY)
                water_discharge_morning = self._get_metric_value(
                    morning_data, HydrologicalMetricName.WATER_DISCHARGE_DAILY
                )
                day_dict["water_level_morning"] = water_level_morning
                day_dict["water_discharge_morning"] = water_discharge_morning
                if previous_day_water_level != "--" and water_level_morning != "--":
                    day_dict["trend"] = water_level_morning - previous_day_water_level
                previous_day_water_level = water_level_morning
            else:
                previous_day_water_level = None
                day_dict["water_level_morning"] = "--"
                day_dict["water_discharge_morning"] = "--"

            # get evening data next
            evening_data = self._get_evening_data(daily_data)
            if not evening_data.empty:
                water_level_evening = self._get_metric_value(evening_data, HydrologicalMetricName.WATER_LEVEL_DAILY)
                water_discharge_evening = self._get_metric_value(
                    evening_data, HydrologicalMetricName.WATER_DISCHARGE_DAILY
                )
                day_dict["water_level_evening"] = water_level_evening
                day_dict["water_discharge_evening"] = water_discharge_evening
            else:
                day_dict["water_level_evening"] = "--"
                day_dict["water_discharge_evening"] = "--"

            # finally, get the rest of the daily data, including water level and discharge averages
            ice_phenomena_data = self._get_ice_phenomena(daily_data)
            day_dict["ice_phenomena"] = ice_phenomena_data
            daily_precipitation_data = self._get_daily_precipitation(daily_data)
            day_dict["daily_precipitation"] = daily_precipitation_data

            for metric_name, metric_code in {
                "water_level_average": HydrologicalMetricName.WATER_LEVEL_DAILY_AVERAGE,
                "water_discharge_average": HydrologicalMetricName.WATER_DISCHARGE_DAILY_AVERAGE,
                "water_temperature": HydrologicalMetricName.WATER_TEMPERATURE,
                "air_temperature": HydrologicalMetricName.AIR_TEMPERATURE,
            }.items():
                day_dict[metric_name] = self._get_metric_value(daily_data, metric_code)
            day_dict["date"] = date.strftime("%Y-%m-%d")
            day_dict["id"] = date.strftime("%Y-%m-%d")

            results.append(day_dict)

        results.extend(self._get_daily_data_extremes(results))

        return results

    def get_discharge_data(self) -> list[dict[str, str | float | int]]:
        results = []
        df = self.df

        if self.is_empty:
            return results

        for date in df["date"].unique():
            day_dict = {}
            daily_data = df[df["date"] == date]

            for metric_name, metric_code in {
                "water_level": HydrologicalMetricName.WATER_LEVEL_DECADAL,
                "water_discharge": HydrologicalMetricName.WATER_DISCHARGE_DAILY,
                "cross_section": HydrologicalMetricName.RIVER_CROSS_SECTION_AREA,
            }.items():
                day_dict[metric_name] = self._get_metric_value(daily_data, metric_code)

            day_dict["date"] = date.strftime("%Y-%m-%d")
            day_dict["id"] = date.strftime("%Y-%m-%d")
            results.append(day_dict)

        return results

    def get_decadal_data(self) -> list[dict[int | str, int | float | str]]:
        results = []
        df = self.df

        if self.is_empty:
            return results

        for date in df["date"].unique():
            decade_dict = {}
            decade_data = df[df["date"] == date]

            for metric_name, metric_code in {
                "water_level": HydrologicalMetricName.WATER_LEVEL_DECADE_AVERAGE,
                "water_discharge": HydrologicalMetricName.WATER_DISCHARGE_DECADE_AVERAGE,
            }.items():
                decade_dict[metric_name] = self._get_metric_value(decade_data, metric_code)

            decade_dict["decade"] = calculate_decade_from_day_in_month(date.day)
            decade_dict["id"] = date.strftime("%Y-%m-%d")
            results.append(decade_dict)

        results.append(self._get_monthly_averages_from_decadal_data(results))

        return results
