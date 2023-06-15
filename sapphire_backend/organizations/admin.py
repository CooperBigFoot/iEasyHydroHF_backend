from django.contrib import admin

from .models import Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["name", "country", "year_type", "is_active"]
    list_filter = ["is_active", "is_deleted", "year_type"]
    search_fields = ["name", "description"]
