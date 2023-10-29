from django.db import models


class SensorQuerySet(models.QuerySet):
    def for_station(self, station_uuid: str):
        return self.filter(station=station_uuid)
