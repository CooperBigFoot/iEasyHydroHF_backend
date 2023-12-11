from django.contrib import admin

from .models import Telegram


@admin.register(Telegram)
class TelegramAdmin(admin.ModelAdmin):
    list_display = ["telegram", "created_date", "hydro_station", "automatically_ingested", "successfully_parsed"]
    list_filter = ["created_date", "automatically_ingested", "hydro_station", "successfully_parsed"]
