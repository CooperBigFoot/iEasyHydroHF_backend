from django.contrib import admin

from .models import BulletinTemplate


@admin.register(BulletinTemplate)
class BulletinTemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "filename", "organization", "created_date", "is_default"]
    list_filter = ["organization", "is_default"]
    readonly_fields = ["uuid", "created_date", "last_modified"]
