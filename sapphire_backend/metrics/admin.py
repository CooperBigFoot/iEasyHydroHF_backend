from django.contrib import admin

from .models import (
    AirTemperature,
    Precipitation,
    WaterDischarge,
    WaterLevel,
    WaterTemperature,
    WaterVelocity,
)


class MetricAdminMixin(admin.ModelAdmin):
    list_display = ["get_station_name", "timestamp", "average_value"]
    list_filter = ["timestamp"]
    delete_selected_confirmation_template = "metrics/delete_selected_confirmation_template.html"

    @staticmethod
    def get_station_name(obj):
        return obj.station.name


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
