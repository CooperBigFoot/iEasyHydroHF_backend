from datetime import datetime
from decimal import Decimal

from dateutil.parser import parse
from tqdm import tqdm

from sapphire_backend.estimations.models import DischargeModel
from sapphire_backend.metrics.models import HydrologicalMetric, MeteorologicalMetric
from sapphire_backend.metrics.timeseries.query import TimeseriesQueryManager
from sapphire_backend.stations.models import HydrologicalStation, MeteorologicalStation
from sapphire_backend.telegrams.models import TelegramReceived
from sapphire_backend.utils.datetime_helper import SmartDatetime


class MetricsDataAnonymizer:
    def __init__(self, station_type: str, src_id: int, dest_id: int, start_date_str: str, end_date_str: str = None):
        self.station_cls = self._get_station_cls(station_type)
        self.src_station = self._get_station(src_id)
        self.dest_station = self._get_station(dest_id)
        self.start_date = self._get_dt(start_date_str)
        self.end_date = (
            self._get_dt(end_date_str) if end_date_str else SmartDatetime(datetime.now(), self.src_station).local
        )

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
            raise ValueError(f"{self.station_cls.__name__} with ID {station_id} does not exist.")

    def _get_dt(self, str_date: str) -> datetime:
        dt_obj = parse(str_date)
        return SmartDatetime(dt_obj.replace(tzinfo=self.src_station.timezone), self.src_station, True).local

    def copy_metrics(self, metric_names: list[str], value_types: list[str], offset_factor: float = 0.0):
        qm = TimeseriesQueryManager(
            model=self._get_metrics_cls(),
            filter_dict={
                "station": self.src_station.id,
                "timestamp_local__gte": self.start_date,
                "timestamp_local__lte": self.end_date,
                "metric_name__in": metric_names,
                "value_type__in": value_types,
            },
        )

        metrics = qm.execute_query()

        for metric_dict in tqdm(metrics.values(), total=metrics.count(), desc="Copying metrics..."):
            cls = self._get_metrics_cls()
            new_metric_dict = {**metric_dict, "station_id": self.dest_station.id}
            if cls == HydrologicalMetric:
                new_metric_dict["avg_value"] = metric_dict["avg_value"] * Decimal(1 + offset_factor)
            else:
                new_metric_dict["value"] = metric_dict["value"] * Decimal(1 + offset_factor)

            new_metric = cls(**new_metric_dict)
            new_metric.save()

    def copy_discharge_curves(self):
        existing_dm = self.src_station.dischargemodel_set.filter(
            valid_from_local__range=(self.start_date, self.end_date)
        )
        for dm in tqdm(existing_dm.values(), total=existing_dm.count(), desc="Copying discharge curves..."):
            new_dm_dict = {**dm, "station_id": self.dest_station.id}
            new_dm_dict.pop("id", None)
            new_dm_dict.pop("uuid", None)
            new_dm = DischargeModel(**new_dm_dict)
            new_dm.save()

    def copy_received_telegrams(self):
        existing_telegrams = TelegramReceived.objects.filter(
            organization=self.src_station.site.organization,
            station_code=self.src_station.station_code,
            created_date__range=(self.start_date, self.end_date),
        )

        for tr in tqdm(existing_telegrams.values(), total=existing_telegrams.count(), desc="Copying telegrams..."):
            telegram_string = tr.pop("telegram")
            telegram_parts = telegram_string.split()
            telegram_parts[0] = self.dest_station.station_code
            updated_telegram_string = " ".join(telegram_parts)

            decoded_values = tr.pop("decoded_values", {})
            if decoded_values:
                decoded_values["raw"] = updated_telegram_string
                decoded_values["section_zero"]["station_code"] = self.dest_station.station_code
                decoded_values["section_zero"]["station_name"] = self.dest_station.name

            new_tr_dict = {
                **tr,
                "telegram": updated_telegram_string,
                "decoded_values": decoded_values,
                "station_code": self.dest_station.station_code,
                "organization_id": self.dest_station.site.organization.id,
                "filestate": None,
            }
            new_tr_dict.pop("id", None)
            new_tr = TelegramReceived(**new_tr_dict)
            new_tr.save()
