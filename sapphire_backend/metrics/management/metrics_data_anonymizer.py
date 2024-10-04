from datetime import datetime

from dateutil.parser import parse

from sapphire_backend.metrics.models import HydrologicalMetric, MeteorologicalMetric
from sapphire_backend.metrics.timeseries.query import TimeseriesQueryManager
from sapphire_backend.stations.models import HydrologicalStation, MeteorologicalStation
from sapphire_backend.utils.datetime_helper import SmartDatetime


class MetricsDataAnonymizer:
    def __init__(self, station_type: str, src_id: int, dest_id: int):
        self.station_cls = self._get_station_cls(station_type)
        self.src_station = self._get_station(src_id)
        self.dest_station = self._get_station(dest_id)

    @staticmethod
    def _get_station_cls(station_type: str) -> type(HydrologicalStation) | type(MeteorologicalStation):
        if station_type == "hydro":
            return HydrologicalStation
        elif station_type == "meteo":
            return MeteorologicalStation
        else:
            raise ValueError(f"Unsupported station type: {station_type}. Expected hydro or meteo.")

    def _get_metrics_cls(self) -> type(HydrologicalMetric) | type(MeteorologicalMetric):
        if self.station_cls == HydrologicalStation:
            return HydrologicalMetric
        else:
            return MeteorologicalMetric

    def _get_station(self, station_id: int) -> HydrologicalStation | MeteorologicalStation:
        try:
            return self.station_cls.objects.get(id=station_id)
        except self.station_cls.DoesNotExist:
            raise ValueError(f"{self.station_cls} with ID {station_id} does not exist.")

    def _get_dt(self, str_date: str) -> datetime:
        dt_obj = parse(str_date)
        return SmartDatetime(dt_obj, self.src_station).local

    def copy_metrics(
        self, start_date_str: str, metric_names: list[str], value_types: list[str], end_date_str: str = None
    ):
        start_date = self._get_dt(start_date_str)
        end_date = (
            self._get_dt(end_date_str) if end_date_str else SmartDatetime(datetime.now(), self.src_station).local
        )
        _ = TimeseriesQueryManager(
            model=self._get_metrics_cls(),
            filter_dict={
                "station_id": self.src_station.id,
                "timestamp_local__gte": start_date,
                "timestamp_local__lte": end_date,
                "metric_name__in": metric_names,
                "value_type__in": value_types,
            },
        )
