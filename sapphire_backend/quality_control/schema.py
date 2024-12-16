from datetime import datetime
from typing import Literal

from django.contrib.auth import get_user_model
from ninja import FilterSchema, Schema

from sapphire_backend.ingestion.models import FileState
from sapphire_backend.metrics.choices import HydrologicalMeasurementType, HydrologicalMetricName
from sapphire_backend.quality_control.models import HistoryLogEntry
from sapphire_backend.telegrams.models import TelegramStored


class HistoryLogFilterSchema(FilterSchema):
    timestamp_local: datetime
    station_id: int
    metric_name: HydrologicalMetricName
    value_type: HydrologicalMeasurementType = HydrologicalMeasurementType.MANUAL
    sensor_identifier: str = ""


class SourceDetailsSchema(Schema):
    display: str | None
    error: str | None
    type: str = Literal["unknown", "user", "telegram", "ingester"]


class HistoryLogOutputSchema(Schema):
    created_date: datetime
    description: str
    value: float
    source_details: SourceDetailsSchema

    @staticmethod
    def resolve_source_details(obj):
        print(obj)
        if obj.source_type == HistoryLogEntry.SourceType.USER:
            User = get_user_model()
            try:
                user = User.objects.get(id=obj.source_id)
                return {
                    "display": user.display_name,
                    "type": "user",
                    "error": None,
                }
            except User.DoesNotExist:
                return {"type": "user", "display": None, "error": "not_found"}

        elif obj.source_type == HistoryLogEntry.SourceType.TELEGRAM:
            # Assuming you have a Telegram model that stores telegram details
            try:
                telegram = TelegramStored.objects.get(id=obj.source_id)
                return {
                    "type": "telegram",
                    "display": telegram.telegram,
                    "error": None,
                }
            except TelegramStored.DoesNotExist:
                return {"type": "telegram", "display": None, "error": "not_found"}

        elif obj.source_type == HistoryLogEntry.SourceType.INGESTER:
            try:
                ingester = FileState.objects.get(id=obj.source_id)
                return {
                    "type": "ingester",
                    "display": ingester.filename,
                    "error": None,
                }
            except FileState.DoesNotExist:
                return {"type": "ingester", "display": None, "error": "not_found"}

        return {
            "type": "unknown",
            "display": None,
            "error": None,
        }
