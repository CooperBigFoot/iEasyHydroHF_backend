from django.contrib import admin

from .models import Telegram


@admin.register(Telegram)
class TelegramAdmin(admin.ModelAdmin):
    list_display = ["telegram", "created_date", "station", "automatically_ingested"]
    list_filter = ["created_date", "automatically_ingested", "station"]
