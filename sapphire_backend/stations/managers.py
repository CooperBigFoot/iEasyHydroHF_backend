from django.db import models


class SensorQuerySet(models.QuerySet):
    def for_station(self, station):
        return self.filter(station=station)
