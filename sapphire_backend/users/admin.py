from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["username", "email", "organization", "user_role"]
    list_filter = ["organization", "user_role"]
    search_fields = ["username", "first_name", "last_name"]
