from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, UserAssignedStation


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ["username", "email", "organization", "user_role", "is_deleted", "is_active"]
    list_filter = ["organization", "user_role", "is_active", "is_deleted"]
    search_fields = ["username", "first_name", "last_name"]

    fieldsets = UserAdmin.fieldsets + (
        (None, {"fields": ("contact_phone", "user_role", "organization", "is_deleted")}),
        (None, {"fields": ("avatar",)}),
    )


@admin.register(UserAssignedStation)
class UserAssignedStationAdmin(admin.ModelAdmin):
    list_display = ["user", "hydro_station", "meteo_station", "virtual_station"]
    list_filter = ["user"]
    search_fields = ["user__username"]
