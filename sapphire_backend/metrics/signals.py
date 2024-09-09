from django.dispatch import Signal, receiver

from sapphire_backend.quality_control.models import HistoryLog

hydro_metric_saved = Signal()
meteo_metric_saved = Signal()


@receiver(hydro_metric_saved)
def hydro_metric_save_handler(sender, instance, created, entry_type, source_id, description, **kwargs):
    if created:
        log = HistoryLog.objects.create(hydro_metric=instance)
    else:
        log = HistoryLog.objects.get(hydro_metric=instance)

    log.create_entry(entry_type, source_id, description)


@receiver(meteo_metric_saved)
def meteo_metric_save_handler(sender, instance, created, entry_type, source_id, description, **kwargs):
    if created:
        log = HistoryLog.objects.create(meteo_metric=instance)
    else:
        log = HistoryLog.objects.get(meteo_metric=instance)

    log.create_entry(entry_type, source_id, description)
