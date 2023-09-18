from django.contrib import admin

from .models import (
    AirTemperature,
    Precipitation,
    SensorStatus,
    WaterDischarge,
    WaterLevel,
    WaterTemperature,
    WaterVelocity,
)


class MetricAdminMixin(admin.ModelAdmin):
    list_display = ["sensor", "get_sensor_station_name", "timestamp", "average_value"]
    list_filter = ["sensor__station__name", "timestamp"]
    delete_selected_confirmation_template = "metrics/delete_selected_confirmation_template.html"

    @staticmethod
    def get_sensor_station_name(obj):
        return obj.sensor.station.name


@admin.register(WaterDischarge)
class WaterDischargeAdmin(MetricAdminMixin):
    pass


@admin.register(WaterLevel)
class WaterLevelAdmin(MetricAdminMixin):
    pass


@admin.register(WaterVelocity)
class WaterVelocityAdmin(MetricAdminMixin):
    pass


@admin.register(WaterTemperature)
class WaterTemperatureAdmin(MetricAdminMixin):
    pass


@admin.register(AirTemperature)
class AirTemperatureAdmin(MetricAdminMixin):
    pass


@admin.register(Precipitation)
class PrecipitationAdmin(MetricAdminMixin):
    pass


@admin.register(SensorStatus)
class SensorStatusAdmin(admin.ModelAdmin):
    list_display = ["sensor", "get_sensor_station_name", "timestamp", "battery_status", "malfunction"]
    list_filter = ["malfunction", "sensor__station__name"]
    delete_selected_confirmation_template = "metrics/delete_selected_confirmation_template.html"

    @staticmethod
    def get_sensor_station_name(obj):
        return obj.sensor.station.name
