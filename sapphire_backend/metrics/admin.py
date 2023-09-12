from django.contrib import admin

from .models import AirTemperature, WaterDischarge, WaterLevel, WaterTemperature, WaterVelocity


class MetricAdminMixin(admin.ModelAdmin):
    list_display = ["station", "timestamp", "value"]
    list_filter = ["station__name", "timestamp"]
    delete_selected_confirmation_template = "metrics/delete_selected_confirmation_template.html"

    def get_deleted_objects(self, objs, request):
        print(objs)
        return super().get_deleted_objects(objs, request)


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
