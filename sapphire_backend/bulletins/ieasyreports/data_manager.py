from datetime import datetime, timedelta
from typing import Any

from ieasyreports.core.tags import DefaultDataManager
from zoneinfo import ZoneInfo


class IEasyHydroDataManager(DefaultDataManager):
    data_cache = {}

    @classmethod
    def get_daily_water_level(
        cls, station_ids: list[int], start_date: datetime, end_date: datetime, **kwargs
    ) -> dict[int, Any]:
        from sapphire_backend.metrics.choices import HydrologicalMeasurementType, HydrologicalMetricName
        from sapphire_backend.metrics.models import HydrologicalMetric
        from sapphire_backend.metrics.timeseries.query import TimeseriesQueryManager

        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        cache_key = f"water_level_daily_data_{'_'.join(map(str, station_ids))}_{start_date_str}_{end_date_str}"

        if cache_key in cls.data_cache:
            return cls.data_cache[cache_key]

        daily_water_level_filter_dict = {
            "station__in": station_ids,
            "timestamp_local__gte": start_date_str,
            "timestamp_local__lt": end_date_str,
            "metric_name__in": [
                HydrologicalMetricName.WATER_LEVEL_DAILY.value,
            ],
            "value_type__in": HydrologicalMeasurementType.MANUAL.value,
        }

        daily_water_level_data = TimeseriesQueryManager(
            model=HydrologicalMetric,
            order_param="timestamp_local",
            order_direction="ASC",
            filter_dict=daily_water_level_filter_dict,
        ).execute_query()

        organized_water_level_data = {}
        for entry in daily_water_level_data.values("timestamp_local", "avg_value", "station_id"):
            station_id = entry["station_id"]
            timestamp = entry["timestamp_local"]
            if station_id not in organized_water_level_data:
                organized_water_level_data[station_id] = {}
            organized_water_level_data[station_id][timestamp] = entry["avg_value"]

        cls.data_cache[cache_key] = organized_water_level_data

        return organized_water_level_data

    @classmethod
    def get_water_level_for_tag(
        cls, station_ids: list[int], station_id: int, target_date: datetime, day_offset: int, time_of_day: str
    ) -> Any:
        start_date = target_date - timedelta(days=2)
        end_date = target_date + timedelta(days=1)

        data = cls.get_daily_water_level(station_ids, start_date, end_date)
        target_timestamp = datetime(
            target_date.year,
            target_date.month,
            target_date.day,
            8 if time_of_day == "morning" else 20,
            tzinfo=ZoneInfo("UTC"),
        ) - timedelta(days=day_offset)

        station_data = data.get(station_id, {})
        return station_data.get(target_timestamp, "-")

    @classmethod
    def get_water_level_trend_value(
        cls, station_ids: list[int], station_id: int, target_date: datetime, time_of_day: str
    ) -> Any:
        current_value = cls.get_water_level_for_tag(station_ids, station_id, target_date, 0, time_of_day)
        previous_value = cls.get_water_level_for_tag(station_ids, station_id, target_date, 1, time_of_day)
        if current_value == "-" or previous_value == "-":
            return "-"
        return current_value - previous_value

    @classmethod
    def get_daily_discharge(
        cls, station_ids: list[int], start_date: datetime, end_date: datetime, **kwargs
    ) -> dict[int, Any]:
        pass
