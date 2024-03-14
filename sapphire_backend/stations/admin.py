from django.contrib import admin

from .models import HydrologicalStation, MeteorologicalStation, Remark, Site, VirtualStation, VirtualStationAssociation


class HydroStationInline(admin.TabularInline):
    model = HydrologicalStation


class MeteoStationInline(admin.TabularInline):
    model = MeteorologicalStation


class VirtualStationAssociationInline(admin.TabularInline):
    model = VirtualStationAssociation


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ["organization", "basin", "region", "uuid"]
    list_filter = ["organization", "basin", "region"]
    readonly_fields = ["uuid"]
    inlines = [HydroStationInline, MeteoStationInline]


class RemarkInline(admin.TabularInline):
    model = Remark


@admin.register(HydrologicalStation)
class HydrologicalStationAdmin(admin.ModelAdmin):
    list_display = ["name", "station_code", "station_type", "site", "uuid"]
    list_filter = ["site__basin", "site__region", "site__organization", "station_type", "is_deleted"]
    readonly_fields = ["uuid"]
    inlines = [RemarkInline, VirtualStationAssociationInline]


@admin.register(MeteorologicalStation)
class MeteorologicalStationAdmin(admin.ModelAdmin):
    list_display = ["name", "station_code", "site", "uuid"]
    list_filter = ["site__basin", "site__region", "site__organization", "is_deleted"]
    readonly_fields = ["uuid"]
    inlines = [RemarkInline]


@admin.register(Remark)
class RemarkAdmin(admin.ModelAdmin):
    list_display = ["hydro_station", "meteo_station", "user", "created_date"]
    list_filter = ["created_date"]
    readonly_fields = ["uuid", "created_date", "last_modified"]


@admin.register(VirtualStation)
class VirtualStationAdmin(admin.ModelAdmin):
    list_display = ["name", "country", "uuid"]
    list_filter = ["country", "basin", "organization", "region", "is_deleted"]
    readonly_fields = ["uuid"]
    exclude = ["hydro_stations"]
    inlines = [VirtualStationAssociationInline]
