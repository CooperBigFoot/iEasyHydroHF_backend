from datetime import datetime, timedelta
from typing import Any

from ieasyreports.core.tags import DefaultDataManager


class IEasyHydroDataManager(DefaultDataManager):
    data_cache = {}

    @classmethod
    def get_daily_water_level(cls, station_ids: list[int], target_date: datetime, **kwargs) -> dict[str, Any]:
        from sapphire_backend.metrics.choices import HydrologicalMeasurementType, HydrologicalMetricName
        from sapphire_backend.metrics.models import HydrologicalMetric
        from sapphire_backend.metrics.timeseries.query import TimeseriesQueryManager

        start_date = (target_date - timedelta(days=2)).strftime("%Y-%m-%d")
        end_date = (target_date + timedelta(days=1)).strftime("%Y-%m-%d")

        cache_key = f"water_level_daily_data_{'_'.join(map(str, station_ids))}_{start_date}_{end_date}"

        if cache_key in cls.data_cache:
            return cls.data_cache[cache_key]

        daily_water_level_filter_dict = {
            "station__in": station_ids,
            "timestamp_local__gte": start_date,
            "timestamp_local__lt": end_date,
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

        cls.data_cache[cache_key] = daily_water_level_data

        return daily_water_level_data
