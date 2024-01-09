from django.contrib import admin

from .models import HydrologicalStation, MeteorologicalStation, Remark, Site


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ["organization", "basin", "region", "uuid"]
    list_filter = ["organization", "basin", "region"]
    readonly_fields = ["uuid"]


@admin.register(HydrologicalStation)
class HydrologicalStationAdmin(admin.ModelAdmin):
    list_display = ["name", "station_code", "site", "uuid"]
    list_filter = ["site__basin", "site__region", "site__organization", "station_type"]
    readonly_fields = ["uuid"]


@admin.register(MeteorologicalStation)
class MeteorologicalStationAdmin(admin.ModelAdmin):
    list_display = ["name", "station_code", "site", "uuid"]
    list_filter = ["site__basin", "site__region", "site__organization"]
    readonly_fields = ["uuid"]


@admin.register(Remark)
class RemarkAdmin(admin.ModelAdmin):
    list_display = ["hydro_station", "meteo_station", "user", "created_date"]
    list_filter = ["created_date"]
    readonly_fields = ["uuid", "created_date", "last_modified"]
