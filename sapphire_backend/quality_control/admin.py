from django.contrib import admin

from .models import HistoryLogEntry


@admin.register(HistoryLogEntry)
class HistoryLogEntryAdmin(admin.ModelAdmin):
    list_display = [
        "created_date",
        "timestamp_local",
        "value",
        "metric_name",
        "station_id",
        "source_type",
        "source_id",
    ]
    list_filter = ["source_type"]
