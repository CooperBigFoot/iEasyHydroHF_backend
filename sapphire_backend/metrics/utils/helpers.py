from datetime import datetime, timezone
from math import ceil

import pandas as pd

from sapphire_backend.metrics.choices import NormType
from sapphire_backend.metrics.managers import HydrologicalNormQuerySet, MeteorologicalNormQuerySet
from sapphire_backend.organizations.models import Organization
from sapphire_backend.utils.daily_precipitation_mapper import DailyPrecipitationCodeMapper
from sapphire_backend.utils.datetime_helper import SmartDatetime
from sapphire_backend.utils.ice_phenomena_mapper import IcePhenomenaCodeMapper
from sapphire_backend.utils.rounding import hydrological_round

from ...stations.models import HydrologicalStation, MeteorologicalStation, VirtualStation
from ..choices import HydrologicalMetricName, MeteorologicalMetricName


class PentadDecadeHelper:
    days_in_pentad = [3, 8, 13, 18, 23, 28]
    days_in_decade = [5, 15, 25]

    @classmethod
    def calculate_decade_date(cls, ordinal_number: int) -> datetime:
        """
        Construct a datetime object from a given ordinal number of a decade in a year

        :param ordinal_number:
        integer representing the absolute ordinal number of the decade in a year, ranged from 1 to 36
        :return: datetime object for the given ordinal number
        """
        idx = (ordinal_number - 1) % 3
        month_increment = (ordinal_number - 1) // 3

        month = month_increment + 1
        day = cls.days_in_decade[idx]

        return datetime(datetime.utcnow().year, month, day, 12, tzinfo=timezone.utc)

    @classmethod
    def calculate_decade_from_the_day_in_month(cls, day: int) -> int:
        """
        Calculate the decade in a month from a given integer number representing a day in the month

        :param day: integer representing the day in month
        :return: integer representing the decade in a month, ranged from 1 to 3
        """
        if 1 <= day <= 31:
            return (day - 1) // 10 + 1 if day <= 20 else 3
        else:
            raise ValueError(f"Day {day} is an invalid day")

    @classmethod
    def calculate_associated_decade_day_for_the_day_in_month(cls, day: int) -> int:
        """
        Calculate the day in month that the decade is associated with for the given day in month

        :param day: integer representing the day in month
        :return: integer representing the day in a month associated with the decade
        """
        decade_num = cls.calculate_decade_from_the_day_in_month(day)
        return cls.days_in_decade[decade_num - 1]

    @classmethod
    def calculate_decade_from_the_date_in_year(cls, date: datetime) -> int:
        """
        Calculates the absolute decade number in a year from a given datetime object

        :param date: datetime object for which to find the decade
        :return: integer representing the decade in a year, ranged from 1 to 36
        """
        month, day = date.month, date.day
        decade = cls.calculate_decade_from_the_day_in_month(day)

        month_decrement = month - 1
        ordinal_number = month_decrement * 3 + decade

        return ordinal_number

    @classmethod
    def calculate_pentad_ordinal_number_from_the_day_in_month(cls, day: int) -> int:
        """
        Calculate the pentad in a month from a given integer number representing a day in the month

        :param day: integer representing the day in month
        :return: integer representing the pentad in a month, ranged from 1 to 6
        """
        if 1 <= day <= 31:
            return (day - 1) // 5 + 1 if day <= 25 else 6
        else:
            raise ValueError(f"Day {day} is an invalid day")

    @classmethod
    def calculate_associated_pentad_day_from_the_day_int_month(cls, day: int) -> int:
        """
        Calculate the day in month that the pentad is associated with for the given day in month

        :param day: integer representing the day in month
        :return: integer representing the day in a month associated with the pentad
        """
        pentad_num = cls.calculate_pentad_ordinal_number_from_the_day_in_month(day)
        return cls.days_in_pentad[pentad_num - 1]


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
            try:
                metric_value = data[data["metric_name"] == metric]["avg_value"]
            except KeyError:
                metric_value = data[data["metric_name"] == metric]["value"]
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

    @staticmethod
    def _get_meteo_decade_aggregation_data(decadal_data: list[dict[int | str, int | float | str]]):
        avg_row = {"id": "agg", "decade": "values"}
        temperature_values = [row["temperature"] for row in decadal_data if row["temperature"] != "--"]
        if temperature_values:
            avg_value = sum(temperature_values) / len(temperature_values)
            avg_row["temperature"] = round(avg_value, 1)
        else:
            avg_row["temperature"] = "--"
        precipitation_values = [row["precipitation"] for row in decadal_data if row["precipitation"] != "--"]
        if precipitation_values:
            sum_value = sum(precipitation_values)
            avg_row["precipitation"] = round(sum_value, 1)
        else:
            avg_row["precipitation"] = "--"

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
            print(f"date: {date}")
            daily_data = df[df["date"] == date]
            day_dict = {}

            # get morning data first
            morning_data = self._get_morning_data(daily_data)
            if not morning_data.empty:
                water_level_morning = self._get_metric_value(morning_data, HydrologicalMetricName.WATER_LEVEL_DAILY)
                water_discharge_morning = self._get_metric_value(
                    morning_data, HydrologicalMetricName.WATER_DISCHARGE_DAILY
                )
                print(f"previous: {previous_day_water_level}")
                print(f"water_level_morning: {water_level_morning}")
                day_dict["water_level_morning"] = water_level_morning
                day_dict["water_discharge_morning"] = water_discharge_morning
                if previous_day_water_level and previous_day_water_level != "--" and water_level_morning != "--":
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

    def get_meteo_decadal_data(self) -> list[dict[int | str, int | float | str]]:
        results = []
        df = self.df

        if self.is_empty:
            return results

        for date in df["date"].unique():
            decade_dict = {}
            decade_data = df[df["date"] == date]
            for metric_name, metric_code in {
                "temperature": MeteorologicalMetricName.AIR_TEMPERATURE_DECADE_AVERAGE,
                "precipitation": MeteorologicalMetricName.PRECIPITATION_DECADE_AVERAGE,
            }.items():
                decade_dict[metric_name] = self._get_metric_value(decade_data, metric_code)

            decade_dict["decade"] = PentadDecadeHelper.calculate_decade_from_the_day_in_month(date.day)
            decade_dict["id"] = date.strftime("%Y-%m-%d")
            results.append(decade_dict)

        results.append(self._get_meteo_decade_aggregation_data(results))

        return results

    def get_hydro_decadal_data(self) -> list[dict[int | str, int | float | str]]:
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

            decade_dict["decade"] = PentadDecadeHelper.calculate_decade_from_the_day_in_month(date.day)
            decade_dict["id"] = date.strftime("%Y-%m-%d")
            results.append(decade_dict)

        results.append(self._get_monthly_averages_from_decadal_data(results))

        return results


def create_norm_dataframe(norm_data: HydrologicalNormQuerySet | MeteorologicalNormQuerySet, norm_type: NormType):
    decade_end = 36 if norm_type == norm_type.DECADAL else 12
    if norm_data.exists():
        df = pd.DataFrame(norm_data.values("ordinal_number", "value")).set_index("ordinal_number")
        df["value"] = df["value"].astype(float)
        df = df.transpose()
    else:
        df = pd.DataFrame(columns=range(1, decade_end + 1))

    columns = ["Period"] + list(range(1, decade_end + 1))
    output_df = pd.DataFrame(columns=columns)
    output_df.loc[0, "Period"] = "Value"

    for col in output_df.columns[1:]:
        col_num = int(col)
        if col_num in df.columns:
            value = df.at["value", col_num] if not df.empty else None
            if value is None:
                continue
            output_df.at[0, col] = (
                hydrological_round(value) if isinstance(norm_data, HydrologicalNormQuerySet) else round(value, 2)
            )
        else:
            output_df.at[0, col] = None

    return output_df


def hydro_station_uuids_belong_to_organization_uuid(station_uuids: list[str], org_uuid: str):
    uuids_set = set(station_uuids)
    return (
        len(uuids_set)
        == HydrologicalStation.objects.filter(uuid__in=uuids_set, site__organization__uuid=org_uuid).count()
    )


def meteo_station_uuids_belong_to_organization_uuid(station_uuids: list[str], org_uuid: str):
    uuids_set = set(station_uuids)
    return (
        len(uuids_set)
        == MeteorologicalStation.objects.filter(uuid__in=uuids_set, site__organization__uuid=org_uuid).count()
    )


def virtual_station_uuids_belong_to_organization_uuid(station_uuids: list[str], org_uuid: str):
    uuids_set = set(station_uuids)
    return len(uuids_set) == VirtualStation.objects.filter(uuid__in=uuids_set, organization__uuid=org_uuid).count()


class HydrologicalYearResolver:
    def __init__(self, organization: Organization, year: int):
        self.organization = organization
        self.year = year

    @property
    def is_calendar_year(self):
        return self.organization.year_type == Organization.YearType.CALENDAR

    @property
    def is_hydrological_year(self):
        return self.organization.year_type == Organization.YearType.HYDROLOGICAL

    def get_start_date(self) -> datetime:
        if self.is_calendar_year:
            return SmartDatetime(datetime(self.year, 1, 1), self.organization).local
        else:
            return SmartDatetime(datetime(self.year - 1, 10, 1), self.organization).local

    def get_end_date(self) -> datetime:
        if self.is_calendar_year:
            return SmartDatetime(datetime(self.year + 1, 1, 1), self.organization).local
        else:
            return SmartDatetime(datetime(self.year, 10, 1), self.organization).local
