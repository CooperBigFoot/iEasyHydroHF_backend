from django.apps import AppConfig


class MetricsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sapphire_backend.metrics"

    def ready(self):
        # register the signals
        pass
