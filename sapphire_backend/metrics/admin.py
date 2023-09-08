from django.contrib import admin

from .models import AirTemperature, WaterDischarge, WaterLevel, WaterTemperature, WaterVelocity


class MetricAdminMixin(admin.ModelAdmin):
    @admin.display(description="Timestamp")
    def formatted_timestamp(self, obj):
        return obj.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    list_display = ["station", "formatted_timestamp", "value"]
    list_filter = ["station__name", "timestamp"]


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
