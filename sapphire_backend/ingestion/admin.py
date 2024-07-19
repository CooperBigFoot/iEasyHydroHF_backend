from django.contrib import admin

from .models import FileState


@admin.register(FileState)
class FileStateAdmin(admin.ModelAdmin):
    list_display = ["filename", "state", "remote_path", "local_path", "state_timestamp", "ingester_name"]
    list_filter = ["state_timestamp", "state", "ingester_name"]
