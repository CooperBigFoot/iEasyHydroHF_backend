from django.db.models import QuerySet

from .choices import HydrologicalMeasurementType, NormType


class TimeSeriesQuerySet(QuerySet):
    def for_metric(self, metric_name: str):
        return self.filter(metric_name=metric_name)

    def for_station(self, station_id: int):
        return self.filter(station_id=station_id)

    def for_type(self, value_type: str):
        return self.filter(value_type=value_type)


class HydrologicalMetricQuerySet(TimeSeriesQuerySet):
    def automatic(self):
        return self.filter(value_type=HydrologicalMeasurementType.AUTOMATIC)

    def manual(self):
        return self.filter(value_type=HydrologicalMeasurementType.MANUAL)

    def for_sensor(self, sensor_identifier: str):
        return self.filter(sensor_identifier=sensor_identifier)


class MeteorologicalMetricQuerySet(TimeSeriesQuerySet):
    pass


class DischargeNormQuerySet(QuerySet):
    def for_station(self, station_uuid: str):
        return self.filter(station=station_uuid)

    def decadal(self):
        return self.filter(norm_type=NormType.DECADAL)

    def monthly(self):
        return self.filter(norm_type=NormType.MONTHLY)
