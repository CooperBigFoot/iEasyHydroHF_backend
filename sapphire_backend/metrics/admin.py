from django.contrib import admin

from .models import HydrologicalMetric, HydrologicalNorm, MeteorologicalMetric, MeteorologicalNorm


@admin.register(HydrologicalMetric)
class HydrologicalMetricAdmin(admin.ModelAdmin):
    list_display = ["station", "timestamp", "avg_value", "metric_name", "value_type"]
    list_filter = ["metric_name", "value_type", "timestamp"]


@admin.register(MeteorologicalMetric)
class MeteorologicalMetricAdmin(admin.ModelAdmin):
    list_display = ["station", "timestamp", "value", "metric_name", "value_type"]
    list_filter = ["metric_name", "value_type", "timestamp"]


@admin.register(HydrologicalNorm)
class HydrologicalNormAdmin(admin.ModelAdmin):
    list_display = ["station", "value", "ordinal_number", "norm_type"]
    list_filter = ["norm_type"]


@admin.register(MeteorologicalNorm)
class MeteorologicalNormAdmin(admin.ModelAdmin):
    list_display = ["station", "value", "ordinal_number", "norm_type", "norm_metric"]
    list_filter = ["norm_type", "norm_metric"]
