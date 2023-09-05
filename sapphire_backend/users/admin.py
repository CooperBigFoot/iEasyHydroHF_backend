from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ["username", "email", "organization", "user_role", "is_deleted", "is_active"]
    list_filter = ["organization", "user_role", "is_active", "is_deleted"]
    search_fields = ["username", "first_name", "last_name"]

    fieldsets = UserAdmin.fieldsets + (
        (None, {"fields": ("contact_phone", "user_role", "organization", "is_deleted")}),
        (None, {"fields": ("avatar",)}),
    )
