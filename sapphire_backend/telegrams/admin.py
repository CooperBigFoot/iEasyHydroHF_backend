from django.contrib import admin

from .models import TelegramParserLog, TelegramReceived, TelegramStored


@admin.register(TelegramReceived)
class TelegramReceivedAdmin(admin.ModelAdmin):
    list_display = [
        "telegram",
        "created_date",
        "valid",
        "errors",
        "acknowledged",
        "acknowledged_ts",
        "acknowledged_by",
        "filestate",
        "station_code",
        "organization",
    ]
    list_filter = [
        "created_date",
        "valid",
        "acknowledged",
        "acknowledged_ts",
        "acknowledged_by",
        "station_code",
        "organization",
    ]


@admin.register(TelegramStored)
class TelegramStoredAdmin(admin.ModelAdmin):
    list_display = ["telegram", "created_date", "telegram_day", "station_code", "stored_by", "auto_stored"]
    list_filter = ["created_date", "organization", "telegram_day", "station_code", "stored_by", "auto_stored"]


@admin.register(TelegramParserLog)
class TelegramParserLogAdmin(admin.ModelAdmin):
    list_display = ["telegram", "created_date", "station_code", "errors", "decoded_values", "valid", "user"]
    list_filter = ["created_date", "station_code", "valid", "user"]
