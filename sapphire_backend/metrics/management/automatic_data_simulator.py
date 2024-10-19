from datetime import datetime
from decimal import Decimal
from random import uniform

from sapphire_backend.metrics.choices import HydrologicalMetricName
from sapphire_backend.metrics.models import HydrologicalMeasurementType, HydrologicalMetric
from sapphire_backend.stations.models import HydrologicalStation
from sapphire_backend.utils.datetime_helper import SmartDatetime
from sapphire_backend.utils.mixins.models import SourceTypeMixin


class AutomaticDataSimulator:
    def __init__(self, src_id: int, dest_id: int):
        self.src_station = self._get_source_station(src_id)
        self.dest_station = self._get_target_station(dest_id)
        self.date = self._get_dt()

    @staticmethod
    def _get_source_station(station_id: int) -> HydrologicalStation:
        try:
            return HydrologicalStation.objects.get(id=station_id, station_type=HydrologicalStation.StationType.MANUAL)
        except HydrologicalStation.DoesNotExist:
            raise ValueError(f"Manual station with ID {station_id} does not exist")

    @staticmethod
    def _get_target_station(station_id: int) -> HydrologicalStation:
        try:
            return HydrologicalStation.objects.get(
                id=station_id, station_type=HydrologicalStation.StationType.AUTOMATIC
            )
        except HydrologicalStation.DoesNotExist:
            raise ValueError(f"Automatic station with ID {station_id} does not exist")

    def _get_dt(self) -> datetime:
        return SmartDatetime(datetime.now(tz=self.src_station.timezone), self.src_station, True).local

    @staticmethod
    def _get_value_with_offset(value: Decimal, offset: float) -> Decimal:
        return value * Decimal(1 + uniform(-offset, offset))

    def _get_fallback_metric(self, metric_name: HydrologicalMetricName) -> HydrologicalMetric | None:
        return HydrologicalMetric.objects.filter(
            metric_name=metric_name,
            value_type=HydrologicalMeasurementType.MANUAL,
            station=self.src_station,
            timestamp_local__day=self.date.day,
            timestamp_local__month=self.date.month,
        ).first()

    def _get_latest_automatic_measurement(self, metric_name: HydrologicalMetricName) -> HydrologicalMetric | None:
        return HydrologicalMetric.objects.filter(
            metric_name=metric_name,
            value_type=HydrologicalMeasurementType.AUTOMATIC,
            station=self.dest_station,
            timestamp_local__day=self.date.day,
            timestamp_local__month=self.date.month,
        ).first()

    def create_simulated_measurement(
        self, metric: HydrologicalMetricName, offset: float = 0.0
    ) -> HydrologicalMetric | None:
        base_metric = self._get_latest_automatic_measurement(metric) or self._get_fallback_metric(metric)
        if not base_metric:
            return

        offset_value = self._get_value_with_offset(base_metric.avg_value, offset)

        simulated_metric = HydrologicalMetric(
            timestamp_local=self.date,
            min_value=None,
            avg_value=offset_value,
            max_value=None,
            unit=base_metric.unit,
            value_type=HydrologicalMeasurementType.AUTOMATIC,
            metric_name=base_metric.metric_name,
            station=self.dest_station,
            sensor_identifier="",
            sensor_type="",
            source_type=SourceTypeMixin.SourceType.UNKNOWN,
            source_id=0,
        )
        simulated_metric.save()
        return simulated_metric
