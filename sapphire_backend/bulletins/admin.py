from django.contrib import admin

from .models import BulletinTemplate, BulletinTemplateTag


@admin.register(BulletinTemplate)
class BulletinTemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "filename", "organization", "created_date", "is_default"]
    list_filter = ["organization", "is_default"]


@admin.register(BulletinTemplateTag)
class BulletinTemplateTagAdmin(admin.ModelAdmin):
    list_display = ["name", "organization"]
    list_filter = ["organization"]
