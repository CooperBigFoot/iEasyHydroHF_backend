from django.contrib import admin

from .models import HistoryLogEntry


@admin.register(HistoryLogEntry)
class HistoryLogEntryAdmin(admin.ModelAdmin):
    list_display = [
        "created_date",
        "timestamp_local_display",  # Use the custom display method
        "metric_name",
        "station_id",
        "previous_value",
        "new_value",
    ]
    list_filter = ["previous_source_type", "new_source_type"]

    def timestamp_local_display(self, obj):
        return obj.timestamp_local.replace(tzinfo=None)
