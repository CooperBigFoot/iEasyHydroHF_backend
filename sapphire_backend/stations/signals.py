from sapphire_backend.stations.models import Sensor, Station


def create_default_sensor(instance: Station, created: bool, *args, **kwargs):
    if created:
        Sensor.objects.create(station=instance)
