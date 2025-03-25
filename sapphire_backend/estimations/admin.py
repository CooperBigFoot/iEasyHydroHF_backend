from django.contrib import admin

from .models import DischargeCalculationPeriod, DischargeModel


@admin.register(DischargeModel)
class DischargeModelAdmin(admin.ModelAdmin):
    list_display = ("name", "param_a", "param_b", "param_c", "valid_from_local", "station")
    search_fields = ("name", "station__station_code")
    list_filter = ("valid_from_local", "station__station_code")
    ordering = ("-valid_from_local",)


@admin.register(DischargeCalculationPeriod)
class DischargeCalculationPeriodAdmin(admin.ModelAdmin):
    list_display = ("station", "is_active", "state", "reason", "start_date_local", "end_date_local", "user")
    list_filter = ("state", "reason", "station__station_code", "is_active")
    search_fields = ("station__station_code", "station__name", "comment")
    ordering = ("-start_date_local",)
    readonly_fields = ("created_date", "last_modified")
