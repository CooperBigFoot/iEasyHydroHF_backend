from django.apps import AppConfig
from django.db.models.signals import post_save


class StationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sapphire_backend.stations"

    def ready(self) -> None:
        from sapphire_backend.stations.models import Station
        from sapphire_backend.stations.signals import create_default_sensor

        post_save.connect(create_default_sensor, Station)
