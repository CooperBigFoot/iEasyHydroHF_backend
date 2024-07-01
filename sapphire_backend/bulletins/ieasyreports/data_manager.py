from datetime import datetime, timedelta
from typing import Any

from ieasyreports.core.tags import DefaultDataManager
from zoneinfo import ZoneInfo


class IEasyHydroDataManager(DefaultDataManager):
    data_cache = {}

    @classmethod
    def resolve_model_mapping(cls, data_type: str) -> dict[str, Any]:
        from sapphire_backend.estimations.models import (
            EstimationsWaterDischargeDaily,
            EstimationsWaterDischargeDailyAverage,
            EstimationsWaterDischargeDecadeAverage,
            EstimationsWaterDischargeFivedayAverage,
            EstimationsWaterLevelDailyAverage,
        )
        from sapphire_backend.metrics.choices import HydrologicalMeasurementType, HydrologicalMetricName
        from sapphire_backend.metrics.models import HydrologicalMetric

        mapping = {
            "water_level_daily": {
                "model": HydrologicalMetric,
                "value_type": HydrologicalMeasurementType.MANUAL,
                "metric_name": HydrologicalMetricName.WATER_LEVEL_DAILY,
            },
            "water_level_average": {
                "model": EstimationsWaterLevelDailyAverage,
                "value_type": HydrologicalMeasurementType.ESTIMATED,
                "metric_name": HydrologicalMetricName.WATER_LEVEL_DAILY_AVERAGE,
            },
            "water_level_measurement": {
                "model": HydrologicalMetric,
                "value_type": HydrologicalMeasurementType.MANUAL,
                "metric_name": HydrologicalMetricName.WATER_LEVEL_DECADAL,
            },
            "discharge_daily": {
                "model": EstimationsWaterDischargeDaily,
                "value_type": HydrologicalMeasurementType.ESTIMATED,
                "metric_name": HydrologicalMetricName.WATER_DISCHARGE_DAILY,
            },
            "discharge_measurement": {
                "model": HydrologicalMetric,
                "value_type": HydrologicalMeasurementType.MANUAL,
                "metric_name": HydrologicalMetricName.WATER_DISCHARGE_DAILY,
            },
            "discharge_average": {
                "model": EstimationsWaterDischargeDailyAverage,
                "value_type": HydrologicalMeasurementType.ESTIMATED,
                "metric_name": HydrologicalMetricName.WATER_DISCHARGE_DAILY_AVERAGE,
            },
            "discharge_pentad": {
                "model": EstimationsWaterDischargeFivedayAverage,
                "value_type": HydrologicalMeasurementType.ESTIMATED,
                "metric_name": HydrologicalMetricName.WATER_DISCHARGE_FIVEDAY_AVERAGE,
            },
            "discharge_decade": {
                "model": EstimationsWaterDischargeDecadeAverage,
                "value_type": HydrologicalMeasurementType.ESTIMATED,
                "metric_name": HydrologicalMetricName.WATER_DISCHARGE_DECADE_AVERAGE,
            },
        }

        return mapping[data_type]

    @classmethod
    def get_metrics_data(
        cls, data_type: str, station_ids: list[int], start_date: datetime, end_date: datetime, **kwargs
    ) -> dict[int, Any]:
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        cache_key = f"{data_type}_{','.join(map(str, station_ids))}_{start_date_str}_{end_date_str}"
        if cache_key in cls.data_cache:
            return cls.data_cache[cache_key]

        model_mapping = cls.resolve_model_mapping(data_type)

        data = model_mapping["model"].objects.filter(
            station_id__in=station_ids,
            timestamp_local__range=[start_date, end_date],
            value_type=model_mapping["value_type"],
            metric_name=model_mapping["metric_name"],
        )

        organized_data = {}
        for entry in data.values("timestamp_local", "avg_value", "station_id"):
            station_id = entry["station_id"]
            timestamp = entry["timestamp_local"]
            if station_id not in organized_data:
                organized_data[station_id] = {}
            organized_data[station_id][timestamp] = entry["avg_value"]

        cls.data_cache[cache_key] = organized_data

        return organized_data

    @classmethod
    def get_metric_value_for_tag(
        cls,
        data_type: str,
        station_ids: list[int],
        station_id: int,
        target_date: datetime,
        day_offset: int,
        time_of_day: str,
    ) -> Any:
        start_date = target_date - timedelta(days=2)
        end_date = target_date + timedelta(days=1)
        data = cls.get_metrics_data(data_type, station_ids, start_date, end_date)

        if time_of_day is not None:
            hour = 8 if time_of_day == "morning" else 20
        else:
            hour = 12

        target_timestamp = datetime(
            target_date.year, target_date.month, target_date.day, hour, tzinfo=ZoneInfo("UTC")
        ) - timedelta(days=day_offset)

        station_data = data.get(station_id, {})

        return station_data.get(target_timestamp, "-")

    @classmethod
    def get_trend_value(
        cls, data_type: str, station_ids: list[int], station_id: int, target_date: datetime, time_of_day: str | None
    ):
        current_value = cls.get_metric_value_for_tag(data_type, station_ids, station_id, target_date, 0, time_of_day)
        previous_value = cls.get_metric_value_for_tag(data_type, station_ids, station_id, target_date, 1, time_of_day)
        if current_value == "-" or previous_value == "-":
            return "-"
        return current_value - previous_value
