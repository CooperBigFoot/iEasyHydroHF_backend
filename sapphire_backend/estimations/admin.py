from django.contrib import admin

from .models import DischargeModel


@admin.register(DischargeModel)
class DischargeModelAdmin(admin.ModelAdmin):
    list_display = ("name", "param_a", "param_b", "param_c", "valid_from_local", "station")
    search_fields = ("name", "station__station_code")
    list_filter = ("valid_from_local", "station__station_code")
    ordering = ("-valid_from_local",)
