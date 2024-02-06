from django.contrib import admin

from .models import HydrologicalMetric, MeteorologicalMetric


@admin.register(HydrologicalMetric)
class HydrologicalMetricAdmin(admin.ModelAdmin):
    list_display = ["station", "timestamp", "avg_value", "metric_name", "value_type"]
    list_filter = ["metric_name", "value_type", "timestamp"]


@admin.register(MeteorologicalMetric)
class MeteorologicalMetricAdmin(admin.ModelAdmin):
    list_display = ["station", "timestamp", "value", "metric_name", "value_type"]
    list_filter = ["metric_name", "value_type", "timestamp"]
