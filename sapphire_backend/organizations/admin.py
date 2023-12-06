from django.contrib import admin

from .models import Basin, Organization, Region


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["name", "country", "year_type", "is_active"]
    list_filter = ["is_active", "year_type"]
    search_fields = ["name", "description"]
    readonly_fields = ["uuid"]


@admin.register(Basin)
class BasinAdmin(admin.ModelAdmin):
    list_display = ["name"]
    list_filter = ["organization"]
    search_fields = ["name"]
    readonly_fields = ["uuid"]


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ["name"]
    list_filter = ["organization"]
    search_fields = ["name"]
    readonly_fields = ["uuid"]
