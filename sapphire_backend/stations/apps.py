from django.apps import AppConfig


class StationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sapphire_backend.stations"

    def ready(self) -> None:
        pass
