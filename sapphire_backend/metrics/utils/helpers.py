from datetime import datetime, timezone
from math import ceil
from typing import Any

import pandas as pd

from sapphire_backend.estimations.models import (
    EstimationsAirTemperatureDaily,
    EstimationsWaterDischargeDaily,
    EstimationsWaterDischargeDailyAverage,
    EstimationsWaterDischargeDecadeAverage,
    EstimationsWaterDischargeFivedayAverage,
    EstimationsWaterLevelDailyAverage,
    EstimationsWaterLevelDecadeAverage,
    EstimationsWaterTemperatureDaily,
)
from sapphire_backend.metrics.choices import NormType
from sapphire_backend.metrics.managers import HydrologicalNormQuerySet, MeteorologicalNormQuerySet
from sapphire_backend.organizations.models import Organization
from sapphire_backend.utils.datetime_helper import SmartDatetime
from sapphire_backend.utils.rounding import hydrological_round

from ...stations.models import HydrologicalStation, MeteorologicalStation, VirtualStation
from ..choices import HydrologicalMetricName, MeteorologicalMetricName
from ..models import HydrologicalMetric, MeteorologicalMetric


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

    @classmethod
    def calculate_pentad_date(cls, ordinal_number: int) -> datetime:
        """
        Construct a datetime object from a given ordinal number of a pentad in a year

        :param ordinal_number:
        integer representing the absolute ordinal number of the pentad in a year, ranged from 1 to 72
        :return: datetime object for the given ordinal number
        """
        idx = (ordinal_number - 1) % 6
        month_increment = (ordinal_number - 1) // 6

        month = month_increment + 1
        day = cls.days_in_pentad[idx]

        return datetime(datetime.utcnow().year, month, day, 12, tzinfo=timezone.utc)

    @classmethod
    def calculate_pentad_from_the_date_in_year(cls, date: datetime) -> int:
        """
        Calculates the absolute pentad number in a year from a given datetime object

        :param date: datetime object for which to find the pentad
        :return: integer representing the pentad in a year, ranged from 1 to 72
        """
        month, day = date.month, date.day
        pentad = cls.calculate_pentad_ordinal_number_from_the_day_in_month(day)

        month_decrement = month - 1
        ordinal_number = month_decrement * 6 + pentad

        return ordinal_number


class OperationalJournalDataTransformer:
    def __init__(
        self,
        data: list[dict[str, float | None]],
        target_month: int,
        station: HydrologicalStation | MeteorologicalStation | VirtualStation,
    ):
        self.original_data = data
        self.df = self._convert_data_to_dataframe()
        self.is_empty = self.df.empty
        self.requested_month = target_month
        self.station = station

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

    def _get_metric_value(
        self, data: pd.DataFrame | pd.Series, metric: str, include_metadata: bool = False
    ) -> dict[str, Any]:
        if not data.empty:
            metric_data = data[data["metric_name"] == metric]
            try:
                metric_value = metric_data["avg_value"]
            except KeyError:
                metric_value = metric_data["value"]

            if metric_value.empty:
                return {"value": "--"}

            # Get the value based on metric type
            if metric in [
                HydrologicalMetricName.WATER_LEVEL_DAILY,
                HydrologicalMetricName.WATER_LEVEL_DAILY_AVERAGE,
                HydrologicalMetricName.WATER_LEVEL_DECADE_AVERAGE,
            ]:
                value = ceil(metric_value.iloc[0])
            elif metric in [
                HydrologicalMetricName.WATER_DISCHARGE_DAILY,
                HydrologicalMetricName.WATER_DISCHARGE_DAILY_AVERAGE,
                HydrologicalMetricName.WATER_DISCHARGE_DECADE_AVERAGE,
            ]:
                value = hydrological_round(metric_value.iloc[0])
            else:
                value = round(metric_value.iloc[0], 1) if metric_value.iloc[0] is not None else "--"

            if not include_metadata:
                return {"value": value}

            # Include metadata if requested
            return {
                "value": value,
                "timestamp_local": metric_data.iloc[0]["timestamp_local"],
                "sensor_identifier": metric_data.iloc[0].get("sensor_identifier", ""),
                "has_history": metric_data.iloc[0].get("has_history", False),
            }

        return {"value": "--"}

    @staticmethod
    def _get_ice_phenomena(data: pd.DataFrame | pd.Series) -> dict[str, list | str]:
        result = {"ice_phenomena_values": [], "ice_phenomena_codes": []}
        if not data.empty:
            ice_phenomena_data = data[data["metric_name"] == HydrologicalMetricName.ICE_PHENOMENA_OBSERVATION]
            if not ice_phenomena_data.empty:
                values = ice_phenomena_data[
                    ["avg_value", "value_code", "sensor_identifier", "timestamp_local", "has_history"]
                ].to_dict("records")
                if values:
                    result.update(
                        {
                            "ice_phenomena_values": [v["avg_value"] for v in values],
                            "ice_phenomena_codes": [v["value_code"] for v in values],
                            "sensor_identifiers": [v["sensor_identifier"] for v in values],
                            "timestamps_local": [v["timestamp_local"] for v in values],
                            "has_history": [v["has_history"] for v in values],
                        }
                    )

        return result

    @staticmethod
    def _get_daily_precipitation(data: pd.DataFrame | pd.Series) -> dict[str, float | int | str]:
        result = {"daily_precipitation_value": None, "daily_precipitation_code": None}
        if not data.empty:
            daily_precipitation_data = data[data["metric_name"] == HydrologicalMetricName.PRECIPITATION_DAILY]
            if not daily_precipitation_data.empty:
                value = (
                    daily_precipitation_data[
                        ["avg_value", "value_code", "sensor_identifier", "timestamp_local", "has_history"]
                    ]
                    .iloc[0]
                    .to_dict()
                )
                result.update(
                    {
                        "daily_precipitation_value": value["avg_value"],
                        "daily_precipitation_code": value["value_code"],
                        "sensor_identifier": value["sensor_identifier"],
                        "timestamp_local": value["timestamp_local"],
                        "has_history": value["has_history"],
                    }
                )

        return result

    def _get_daily_data_extremes(self, daily_data: list[dict[str, str | float | int]]) -> list[dict[str, str | float]]:
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

        min_row = {"id": "min", "date": "minimum", "station_id": self.station.id}
        max_row = {"id": "max", "date": "maximum", "station_id": self.station.id}

        for metric in relevant_metrics:
            valid_values = [row[metric]["value"] for row in daily_data if row[metric]["value"] != "--"]
            if valid_values:
                min_row[metric] = {"value": min(valid_values)}
                max_row[metric] = {"value": max(valid_values)}
            else:
                min_row[metric] = {"value": "--"}
                max_row[metric] = {"value": "--"}

        min_row["ice_phenomena"] = {"value": "--"}
        max_row["ice_phenomena"] = {"value": "--"}

        min_row["daily_precipitation"] = {"value": "--"}
        max_row["daily_precipitation"] = {"value": "--"}

        return [min_row, max_row]

    @staticmethod
    def _get_monthly_averages_from_decadal_data(decadal_data: list[dict[int | str, int | float | str]]):
        avg_row = {"id": "avg", "decade": "average"}
        for metric in ["water_level", "water_discharge"]:
            valid_values = [row[metric]["value"] for row in decadal_data if row[metric]["value"] != "--"]
            if valid_values:
                avg_value = sum(valid_values) / len(valid_values)
                avg_row[metric] = {
                    "value": hydrological_round(avg_value) if metric == "water_discharge" else ceil(avg_value)
                }
            else:
                avg_row[metric] = {"value": "--"}

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

    def get_daily_data(self) -> list[dict[str, Any]]:
        results = []
        df = self.df
        results = []
        if self.is_empty:
            return results

        previous_month_last_day = df["date"].min()
        previous_day_water_level = None

        if previous_month_last_day.month != self.requested_month:
            previous_month_last_day_data = df[df["date"] == previous_month_last_day]

            # get morning water_level to be able to calculate the trend on the first day of the given month
            if not previous_month_last_day_data.empty:
                morning_data = self._get_morning_data(previous_month_last_day_data)
                previous_day_water_level = self._get_metric_value(
                    morning_data, HydrologicalMetricName.WATER_LEVEL_DAILY
                )

            # exclude the last day of the previous month from the dataframe
            df = df[df["date"] != previous_month_last_day]

        # iterate over the existing dates
        for date in df["date"].unique():
            daily_data = df[df["date"] == date]
            day_dict = {}

            # get morning data first
            morning_data = self._get_morning_data(daily_data)
            if not morning_data.empty:
                water_level_morning = self._get_metric_value(
                    morning_data, HydrologicalMetricName.WATER_LEVEL_DAILY, True
                )
                water_discharge_morning = self._get_metric_value(
                    morning_data, HydrologicalMetricName.WATER_DISCHARGE_DAILY
                )
                day_dict["water_level_morning"] = water_level_morning
                day_dict["water_discharge_morning"] = water_discharge_morning
                if (
                    previous_day_water_level
                    and previous_day_water_level["value"] != "--"
                    and water_level_morning["value"] != "--"
                ):
                    day_dict["trend"] = water_level_morning["value"] - previous_day_water_level["value"]
                previous_day_water_level = water_level_morning

            else:
                previous_day_water_level = None
                day_dict["water_level_morning"] = {"value": "--"}
                day_dict["water_discharge_morning"] = {"value": "--"}

            # get evening data next
            evening_data = self._get_evening_data(daily_data)
            if not evening_data.empty:
                water_level_evening = self._get_metric_value(
                    evening_data, HydrologicalMetricName.WATER_LEVEL_DAILY, True
                )
                water_discharge_evening = self._get_metric_value(
                    evening_data, HydrologicalMetricName.WATER_DISCHARGE_DAILY
                )
                day_dict["water_level_evening"] = water_level_evening
                day_dict["water_discharge_evening"] = water_discharge_evening
            else:
                day_dict["water_level_evening"] = {"value": "--"}
                day_dict["water_discharge_evening"] = {"value": "--"}

            day_dict["ice_phenomena"] = self._get_ice_phenomena(daily_data)
            day_dict["daily_precipitation"] = self._get_daily_precipitation(daily_data)

            for metric_name, metric_code in {
                "water_level_average": HydrologicalMetricName.WATER_LEVEL_DAILY_AVERAGE,
                "water_discharge_average": HydrologicalMetricName.WATER_DISCHARGE_DAILY_AVERAGE,
                "water_temperature": HydrologicalMetricName.WATER_TEMPERATURE,
                "air_temperature": HydrologicalMetricName.AIR_TEMPERATURE,
            }.items():
                day_dict[metric_name] = self._get_metric_value(
                    daily_data,
                    metric_code,
                    metric_code in (HydrologicalMetricName.WATER_TEMPERATURE, HydrologicalMetricName.AIR_TEMPERATURE),
                )
            day_dict["date"] = date.strftime("%Y-%m-%d")
            day_dict["id"] = date.strftime("%Y-%m-%d")
            day_dict["station_id"] = self.station.id

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
                day_dict[metric_name] = self._get_metric_value(daily_data, metric_code, True)

            day_dict["date"] = date.strftime("%Y-%m-%d")
            day_dict["id"] = date.strftime("%Y-%m-%d")
            day_dict["station_id"] = self.station.id
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
            temperature_data = self._get_metric_value(
                decade_data,
                MeteorologicalMetricName.AIR_TEMPERATURE_DECADE_AVERAGE,
                True,
            )
            precipitation_data = self._get_metric_value(
                decade_data,
                MeteorologicalMetricName.PRECIPITATION_DECADE_AVERAGE,
                True,
            )

            decade_dict = {
                "decade": PentadDecadeHelper.calculate_decade_from_the_day_in_month(date.day),
                "id": date.strftime("%Y-%m-%d"),
                "temperature": temperature_data["value"],
                "precipitation": precipitation_data["value"],
            }
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


class OperationalJournalVirtualDataTransformer(OperationalJournalDataTransformer):
    def _convert_data_to_dataframe(self):
        for entry in self.original_data:
            if isinstance(entry["timestamp_local"], datetime):
                entry["timestamp_local"] = entry["timestamp_local"].replace(tzinfo=None)

        df = pd.DataFrame(self.original_data)

        if not df.empty:
            df["timestamp_local"] = pd.to_datetime(df["timestamp_local"])
            df["date"] = df["timestamp_local"].dt.date
            df["time"] = df["timestamp_local"].dt.strftime("%H:%M")

        return df

    def _get_daily_data_extremes(self, daily_data: list[dict[str, str | float | int]]) -> list[dict[str, str | float]]:
        relevant_metrics = [
            "water_discharge_morning",
            "water_discharge_evening",
            "water_discharge_average",
        ]

        min_row = {"id": "min", "date": "minimum", "station_id": self.station.id}
        max_row = {"id": "max", "date": "maximum", "station_id": self.station.id}

        for metric in relevant_metrics:
            valid_values = [row[metric]["value"] for row in daily_data if row[metric]["value"] != "--"]
            if valid_values:
                min_row[metric] = {"value": min(valid_values)}
                max_row[metric] = {"value": max(valid_values)}
            else:
                min_row[metric] = {"value": "--"}
                max_row[metric] = {"value": "--"}

        return [min_row, max_row]

    def _get_monthly_averages_from_decadal_data(self, decadal_data: list[dict[int | str, int | float | str]]):
        avg_row = {"id": "avg", "decade": "average", "station_id": self.station.id}
        valid_values = [
            row["water_discharge"]["value"] for row in decadal_data if row["water_discharge"]["value"] != "--"
        ]

        if valid_values:
            avg_value = sum(valid_values) / len(valid_values)
            avg_row["water_discharge"] = {"value": hydrological_round(avg_value)}
        else:
            avg_row["water_discharge"] = {"value": "--"}

        return avg_row

    def get_daily_data(self):
        df = self.df
        results = []
        if self.is_empty:
            return results

        # iterate over the existing dates
        for date in df["date"].unique():
            daily_data = df[df["date"] == date]
            day_dict = {}

            # get morning data first
            morning_data = self._get_morning_data(daily_data)
            if not morning_data.empty:
                water_discharge_morning = self._get_metric_value(
                    morning_data, HydrologicalMetricName.WATER_DISCHARGE_DAILY
                )
                day_dict["water_discharge_morning"] = water_discharge_morning
            else:
                day_dict["water_discharge_morning"] = {"value": "--"}

            # get evening data next
            evening_data = self._get_evening_data(daily_data)
            if not evening_data.empty:
                water_discharge_evening = self._get_metric_value(
                    evening_data, HydrologicalMetricName.WATER_DISCHARGE_DAILY
                )
                day_dict["water_discharge_evening"] = water_discharge_evening
            else:
                day_dict["water_discharge_evening"] = {"value": "--"}

            day_dict["water_discharge_average"] = self._get_metric_value(
                daily_data, HydrologicalMetricName.WATER_DISCHARGE_DAILY_AVERAGE
            )

            day_dict["date"] = date.strftime("%Y-%m-%d")
            day_dict["id"] = date.strftime("%Y-%m-%d")
            day_dict["station_id"] = self.station.id

            results.append(day_dict)

        results.extend(self._get_daily_data_extremes(results))

        return results

    def get_hydro_decadal_data(self) -> list[dict[int | str, int | float | str]]:
        results = []
        df = self.df

        if self.is_empty:
            return results

        for date in df["date"].unique():
            decade_dict = {}
            decade_data = df[df["date"] == date]

            decade_dict["water_discharge"] = self._get_metric_value(
                decade_data, HydrologicalMetricName.WATER_DISCHARGE_DECADE_AVERAGE
            )

            decade_dict["decade"] = PentadDecadeHelper.calculate_decade_from_the_day_in_month(date.day)
            decade_dict["id"] = date.strftime("%Y-%m-%d")
            results.append(decade_dict)

        results.append(self._get_monthly_averages_from_decadal_data(results))

        return results


def create_norm_dataframe(norm_data: HydrologicalNormQuerySet | MeteorologicalNormQuerySet, norm_type: NormType):
    if norm_type == NormType.DECADAL:
        decade_end = 36  # 12 months × 3 decades per month
    elif norm_type == NormType.PENTADAL:
        decade_end = 72  # 12 months × 6 pentads per month
    else:  # MONTHLY
        decade_end = 12  # 12 months

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


def save_metric_and_create_log(
    metric_instance: HydrologicalMetric | MeteorologicalMetric, refresh_view: bool = False, description: str = ""
):
    existing = metric_instance.get_existing_record()
    metric_instance.save(refresh_view=refresh_view)
    if existing:
        log = metric_instance.create_log_entry(existing, description)
    else:
        log = None

    return metric_instance, log


class SDKDataHelper:
    def __init__(self, organization: Organization, filters: dict):
        self.organization = organization
        self.filters = filters
        self.metrics_mapping = self._resolve_metrics_to_models()
        self._validate_filters()

    def _validate_filters(self):
        """
        Ensures:
        1. At least one timestamp filter is present
        2. The metric name is present in the mapping

        Raises:
            ValueError: If the filters are invalid.
        """
        # Check if at least one timestamp filter is present
        timestamp_fields = [
            "timestamp_local",
            "timestamp_local__gt",
            "timestamp_local__gte",
            "timestamp_local__lt",
            "timestamp_local__lte",
            "timestamp",
            "timestamp__gt",
            "timestamp__gte",
            "timestamp__lt",
            "timestamp__lte",
        ]

        has_timestamp_filter = any(
            field in self.filters and self.filters[field] is not None for field in timestamp_fields
        )

        if not has_timestamp_filter:
            raise ValueError("At least one timestamp filter must be present")

        # Check if metric_name__in is present and contains valid metric names
        if "metric_name__in" in self.filters and self.filters["metric_name__in"] is not None:
            valid_metric_names = set(self.metrics_mapping.keys())
            invalid_metric_names = [
                metric_name for metric_name in self.filters["metric_name__in"] if metric_name not in valid_metric_names
            ]

            if invalid_metric_names:
                raise ValueError(f"Invalid metric names: {invalid_metric_names}")
        else:
            raise ValueError("metric_name__in filter is required")

    def _resolve_metrics_to_models(self):
        hydro_metrics_mapping = {
            # water levels
            HydrologicalMetricName.WATER_LEVEL_DAILY: [HydrologicalMetric],
            HydrologicalMetricName.WATER_LEVEL_DECADAL: [HydrologicalMetric],
            HydrologicalMetricName.WATER_LEVEL_DAILY_AVERAGE: [EstimationsWaterLevelDailyAverage],
            HydrologicalMetricName.WATER_LEVEL_DECADE_AVERAGE: [EstimationsWaterLevelDecadeAverage],
            # water discharges
            HydrologicalMetricName.WATER_DISCHARGE_DAILY: [HydrologicalMetric, EstimationsWaterDischargeDaily],
            HydrologicalMetricName.WATER_DISCHARGE_DAILY_AVERAGE: [EstimationsWaterDischargeDailyAverage],
            HydrologicalMetricName.WATER_DISCHARGE_FIVEDAY_AVERAGE: [EstimationsWaterDischargeFivedayAverage],
            HydrologicalMetricName.WATER_DISCHARGE_DECADE_AVERAGE: [EstimationsWaterDischargeDecadeAverage],
            # temperatures
            HydrologicalMetricName.WATER_TEMPERATURE: [HydrologicalMetric],
            HydrologicalMetricName.AIR_TEMPERATURE: [HydrologicalMetric],
            HydrologicalMetricName.WATER_TEMPERATURE_DAILY_AVERAGE: [EstimationsWaterTemperatureDaily],
            HydrologicalMetricName.AIR_TEMPERATURE_DAILY_AVERAGE: [EstimationsAirTemperatureDaily],
            # precipitation
            HydrologicalMetricName.PRECIPITATION_DAILY: [HydrologicalMetric],
            # ice phenomena
            HydrologicalMetricName.ICE_PHENOMENA_OBSERVATION: [HydrologicalMetric],
        }

        meteometric_metrics_mapping = {
            MeteorologicalMetricName.AIR_TEMPERATURE_DECADE_AVERAGE: [MeteorologicalMetric],
            MeteorologicalMetricName.PRECIPITATION_DECADE_AVERAGE: [MeteorologicalMetric],
            MeteorologicalMetricName.PRECIPITATION_MONTH_AVERAGE: [MeteorologicalMetric],
            MeteorologicalMetricName.AIR_TEMPERATURE_MONTH_AVERAGE: [MeteorologicalMetric],
        }

        return {
            **hydro_metrics_mapping,
            **meteometric_metrics_mapping,
        }

    def _get_stations_info(self):
        """
        Gets all stations information based on the filters.

        Returns:
            list: A list of dictionaries containing station information.
            Each dictionary contains:
                - id: The station ID
                - uuid: The station UUID
                - station_code: The station code
                - station_type: The station type ('hydro' or 'meteo')
        """
        stations_info = []

        # If station is specified, get that specific station
        if "station" in self.filters and self.filters["station"] is not None:
            station_id = self.filters["station"]

            # Try to get the hydro station
            hydro_station = HydrologicalStation.objects.filter(
                id=station_id, station_type=HydrologicalStation.StationType.MANUAL
            ).first()
            if hydro_station:
                stations_info.append(
                    {
                        "id": hydro_station.id,
                        "uuid": str(hydro_station.uuid),
                        "name": hydro_station.name,
                        "station_code": hydro_station.station_code,
                        "station_type": "hydro",
                    }
                )
                return stations_info

            # Try to get the meteo station
            meteo_station = MeteorologicalStation.objects.filter(id=station_id).first()
            if meteo_station:
                stations_info.append(
                    {
                        "id": meteo_station.id,
                        "uuid": str(meteo_station.uuid),
                        "name": meteo_station.name,
                        "station_code": meteo_station.station_code,
                        "station_type": "meteo",
                    }
                )
                return stations_info

        # If station__in is specified, get those specific stations
        if "station__in" in self.filters and self.filters["station__in"] is not None:
            station_ids = self.filters["station__in"]

            # Get hydro stations
            hydro_stations = HydrologicalStation.objects.filter(
                id__in=station_ids, station_type=HydrologicalStation.StationType.MANUAL
            )
            for station in hydro_stations:
                stations_info.append(
                    {
                        "id": station.id,
                        "uuid": str(station.uuid),
                        "name": station.name,
                        "station_code": station.station_code,
                        "station_type": "hydro",
                    }
                )

            # Get meteo stations
            meteo_stations = MeteorologicalStation.objects.filter(id__in=station_ids)
            for station in meteo_stations:
                stations_info.append(
                    {
                        "id": station.id,
                        "uuid": str(station.uuid),
                        "name": station.name,
                        "station_code": station.station_code,
                        "station_type": "meteo",
                    }
                )

            return stations_info

        # If station__station_code is specified, get stations by code
        if "station__station_code" in self.filters and self.filters["station__station_code"] is not None:
            station_code = self.filters["station__station_code"]

            # Get hydro stations
            hydro_stations = HydrologicalStation.objects.filter(
                station_code=station_code, station_type=HydrologicalStation.StationType.MANUAL
            )
            for station in hydro_stations:
                stations_info.append(
                    {
                        "id": station.id,
                        "uuid": str(station.uuid),
                        "name": station.name,
                        "station_code": station.station_code,
                        "station_type": "hydro",
                    }
                )

            # Get meteo stations
            meteo_stations = MeteorologicalStation.objects.filter(station_code=station_code)
            for station in meteo_stations:
                stations_info.append(
                    {
                        "id": station.id,
                        "uuid": str(station.uuid),
                        "name": station.name,
                        "station_code": station.station_code,
                        "station_type": "meteo",
                    }
                )

            return stations_info

        # If station__station_code__in is specified, get stations by codes
        if "station__station_code__in" in self.filters and self.filters["station__station_code__in"] is not None:
            station_codes = self.filters["station__station_code__in"]

            # Get hydro stations
            hydro_stations = HydrologicalStation.objects.filter(
                station_code__in=station_codes, station_type=HydrologicalStation.StationType.MANUAL
            )
            for station in hydro_stations:
                stations_info.append(
                    {
                        "id": station.id,
                        "uuid": str(station.uuid),
                        "name": station.name,
                        "station_code": station.station_code,
                        "station_type": "hydro",
                    }
                )

            # Get meteo stations
            meteo_stations = MeteorologicalStation.objects.filter(station_code__in=station_codes)
            for station in meteo_stations:
                stations_info.append(
                    {
                        "id": station.id,
                        "uuid": str(station.uuid),
                        "name": station.name,
                        "station_code": station.station_code,
                        "station_type": "meteo",
                    }
                )

            return stations_info

        # If no station filter is specified, get all stations for the organization
        hydro_stations = HydrologicalStation.objects.filter(
            site__organization=self.organization, station_type=HydrologicalStation.StationType.MANUAL
        )
        for station in hydro_stations:
            stations_info.append(
                {
                    "id": station.id,
                    "uuid": str(station.uuid),
                    "name": station.name,
                    "station_code": station.station_code,
                    "station_type": "hydro",
                }
            )

        meteo_stations = MeteorologicalStation.objects.filter(site__organization=self.organization)
        for station in meteo_stations:
            stations_info.append(
                {
                    "id": station.id,
                    "uuid": str(station.uuid),
                    "name": station.name,
                    "station_code": station.station_code,
                    "station_type": "meteo",
                }
            )

        return stations_info

    def get_data(self):
        """
        Queries the data from the models and formats it according to the SDK output schema.

        Returns:
            list: A list of SDKOutputSchema objects.
        """
        # Get the metric names from the filters
        metric_names = self.filters.get("metric_name__in", [])

        # Get all stations info
        stations_info = self._get_stations_info()

        # Initialize the result
        result = []

        # For each station, query the data for each metric name
        for station_info in stations_info:
            station_data = []

            # For each metric name, query the data from each model
            for metric_name in metric_names:
                models = self.metrics_mapping.get(metric_name, [])
                metric_data = []

                # Query each model for the metric name
                for model in models:
                    model_data = self._query_model(model, metric_name, station_info["id"])
                    metric_data.extend(model_data)

                # sort the metric data by timestamp_local
                metric_data.sort(key=lambda x: x["timestamp_local"], reverse=True)

                unit = self._get_metric_unit(metric_name)
                variable = {"variable_code": metric_name, "unit": unit, "values": metric_data if metric_data else []}
                station_data.append(variable)

            # If we have data for this station, add it to the result
            if station_data:
                output = {
                    "station_id": station_info["id"],
                    "station_uuid": station_info["uuid"],
                    "station_code": station_info["station_code"],
                    "station_type": station_info["station_type"],
                    "station_name": station_info["name"],
                    "data": station_data,
                }

                result.append(output)

        return result

    def _query_model(self, model, metric_name, station_id):
        """
        Queries a model for a given metric name and station ID.

        Args:
            model: The model to query.
            metric_name (str): The metric name.
            station_id (int): The station ID.

        Returns:
            list: A list of SDKDataValueSchema objects.
        """
        # Create a copy of the filters
        filters = self.filters.copy()

        # Add the station ID to the filters
        filters["station"] = station_id

        # Add the metric name to the filters
        filters["metric_name"] = metric_name

        # Query the model
        queryset = model.objects.filter(**filters).order_by("-timestamp_local")

        # Convert the queryset to a list of SDKDataValueSchema objects
        result = []

        for obj in queryset:
            # Get the value
            if hasattr(obj, "avg_value"):
                value = obj.avg_value
            elif hasattr(obj, "value"):
                value = obj.value
            else:
                continue

            local_timestamp = obj.timestamp_local.replace(tzinfo=self.organization.timezone)
            utc_timestamp = getattr(
                obj, "timestamp", local_timestamp.replace(tzinfo=self.organization.timezone).astimezone(timezone.utc)
            )

            # Create the value schema
            value_schema = {
                "value_type": getattr(obj, "value_type", None),
                "value": value,
                "timestamp_local": local_timestamp,
                "timestamp_utc": utc_timestamp,
                "value_code": getattr(obj, "value_code", None),
            }

            result.append(value_schema)

        return result

    def _get_metric_unit(self, metric_name):
        """
        Gets the unit for a given metric name.

        Args:
            metric_name (str): The metric name.

        Returns:
            str: The unit.
        """
        from sapphire_backend.metrics.choices import MetricUnit

        # Map metric names to units
        metric_units = {
            # Water levels
            HydrologicalMetricName.WATER_LEVEL_DAILY: MetricUnit.WATER_LEVEL,
            HydrologicalMetricName.WATER_LEVEL_DAILY_AVERAGE: MetricUnit.WATER_LEVEL,
            HydrologicalMetricName.WATER_LEVEL_DECADAL: MetricUnit.WATER_LEVEL,
            HydrologicalMetricName.WATER_LEVEL_DECADE_AVERAGE: MetricUnit.WATER_LEVEL,
            # Water discharges
            HydrologicalMetricName.WATER_DISCHARGE_DAILY: MetricUnit.WATER_DISCHARGE,
            HydrologicalMetricName.WATER_DISCHARGE_DAILY_AVERAGE: MetricUnit.WATER_DISCHARGE,
            HydrologicalMetricName.WATER_DISCHARGE_FIVEDAY_AVERAGE: MetricUnit.WATER_DISCHARGE,
            HydrologicalMetricName.WATER_DISCHARGE_DECADE_AVERAGE: MetricUnit.WATER_DISCHARGE,
            # Temperatures
            HydrologicalMetricName.WATER_TEMPERATURE: MetricUnit.TEMPERATURE,
            HydrologicalMetricName.AIR_TEMPERATURE: MetricUnit.TEMPERATURE,
            HydrologicalMetricName.WATER_TEMPERATURE_DAILY_AVERAGE: MetricUnit.TEMPERATURE,
            HydrologicalMetricName.AIR_TEMPERATURE_DAILY_AVERAGE: MetricUnit.TEMPERATURE,
            # Precipitation
            HydrologicalMetricName.PRECIPITATION_DAILY: MetricUnit.PRECIPITATION,
            # Ice phenomena
            HydrologicalMetricName.ICE_PHENOMENA_OBSERVATION: MetricUnit.ICE_PHENOMENA_OBSERVATION,
            # Meteorological metrics
            MeteorologicalMetricName.AIR_TEMPERATURE_DECADE_AVERAGE: MetricUnit.TEMPERATURE,
            MeteorologicalMetricName.AIR_TEMPERATURE_MONTH_AVERAGE: MetricUnit.TEMPERATURE,
            MeteorologicalMetricName.PRECIPITATION_DECADE_AVERAGE: MetricUnit.PRECIPITATION,
            MeteorologicalMetricName.PRECIPITATION_MONTH_AVERAGE: MetricUnit.PRECIPITATION,
        }

        return metric_units.get(metric_name, "")
