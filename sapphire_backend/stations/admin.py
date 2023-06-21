from django.contrib import admin

from .models import Station


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ["name", "station_code", "region", "basin"]
    list_filter = ["basin", "region", "is_automatic", "station_type", "is_automatic"]
    search_fields = ["name", "region", "basin"]
