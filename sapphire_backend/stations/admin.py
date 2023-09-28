from django.contrib import admin

from .models import Sensor, Station


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ["name", "station_code", "organization", "region", "basin"]
    list_filter = ["basin", "region", "organization", "is_automatic", "station_type", "is_automatic"]
    search_fields = ["name", "region", "basin"]
    readonly_fields = ["uuid"]


@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    list_display = ["name", "station", "identifier", "manufacturer", "is_default"]
    list_filter = ["station__name", "manufacturer", "is_default"]
    search_fields = ["station__name", "manufacturer"]
