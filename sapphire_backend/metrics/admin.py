from django.contrib import admin

from .models import DischargeNorm, HydrologicalMetric, MeteorologicalMetric


@admin.register(HydrologicalMetric)
class HydrologicalMetricAdmin(admin.ModelAdmin):
    list_display = ["station", "timestamp", "avg_value", "metric_name", "value_type"]
    list_filter = ["metric_name", "value_type", "timestamp"]


@admin.register(MeteorologicalMetric)
class MeteorologicalMetricAdmin(admin.ModelAdmin):
    list_display = ["station", "timestamp", "value", "metric_name", "value_type"]
    list_filter = ["metric_name", "value_type", "timestamp"]


@admin.register(DischargeNorm)
class DischargeNormalAdmin(admin.ModelAdmin):
    list_display = ["station", "value", "ordinal_number", "norm_type"]
    list_filter = ["norm_type"]
