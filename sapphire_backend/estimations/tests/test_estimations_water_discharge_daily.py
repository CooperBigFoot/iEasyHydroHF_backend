from datetime import timedelta

from sapphire_backend.estimations.models import EstimationsWaterDischargeDaily
from sapphire_backend.metrics.choices import HydrologicalMeasurementType, HydrologicalMetricName, MetricUnit
from sapphire_backend.metrics.models import HydrologicalMetric
from sapphire_backend.utils.datetime_helper import SmartDatetime
from sapphire_backend.utils.rounding import custom_round


class TestHydroStationWaterDischargeDaily:
    def test_water_discharge_daily_morning(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
    ):
        timestamp = discharge_model_manual_hydro_station_kyrgyz.valid_from_local + timedelta(days=1)
        smart_dt = SmartDatetime(timestamp, station=manual_hydro_station_kyrgyz, tz_included=False)

        water_level_morning = HydrologicalMetric(
            timestamp_local=smart_dt.morning_local,
            avg_value=70,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_hydro_station_kyrgyz,
        )
        water_level_morning.save()

        discharge_morning_expected = discharge_model_manual_hydro_station_kyrgyz.estimate_discharge(
            water_level_morning.avg_value
        )

        discharge_morning_estimated = EstimationsWaterDischargeDaily.objects.get(
            station_id=manual_hydro_station_kyrgyz.id, timestamp_local=smart_dt.morning_local
        ).avg_value

        assert custom_round(discharge_morning_estimated, 6) == custom_round(discharge_morning_expected, 6)

    def test_water_discharge_daily_evening(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
    ):
        timestamp = discharge_model_manual_hydro_station_kyrgyz.valid_from_local + timedelta(days=1)
        smart_dt = SmartDatetime(timestamp, station=manual_hydro_station_kyrgyz, tz_included=False)

        water_level_evening = HydrologicalMetric(
            timestamp_local=smart_dt.evening_local,
            avg_value=135,
            unit=MetricUnit.WATER_LEVEL,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=manual_hydro_station_kyrgyz,
        )
        water_level_evening.save()

        discharge_evening_expected = discharge_model_manual_hydro_station_kyrgyz.estimate_discharge(
            water_level_evening.avg_value
        )

        discharge_evening_estimated = EstimationsWaterDischargeDaily.objects.get(
            station_id=manual_hydro_station_kyrgyz.id, timestamp_local=smart_dt.evening_local
        ).avg_value

        assert custom_round(discharge_evening_estimated, 6) == custom_round(discharge_evening_expected, 6)
