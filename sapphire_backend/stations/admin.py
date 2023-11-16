from django.contrib import admin

from .models import Remark, Sensor, Station


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
    readonly_fields = ["uuid"]


@admin.register(Remark)
class RemarkAdmin(admin.ModelAdmin):
    list_display = ["station", "user", "created_date"]
    list_filter = ["created_date"]
    readonly_fields = ["uuid", "created_date", "last_modified"]
