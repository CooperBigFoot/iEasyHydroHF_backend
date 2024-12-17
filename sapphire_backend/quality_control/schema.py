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
    value: float | None
    value_code: int | None
    error: str | None
    type: str = Literal["unknown", "user", "telegram", "ingester"]


class TimelineEntrySchema(Schema):
    type: str = Literal["initial", "change", "current"]
    created_date: datetime | None
    description: str
    value: float
    value_code: int | None
    source_type: str
    source_id: int
    source_name: str | None = None

    @staticmethod
    def resolve_source_name(obj):
        if obj["source_type"] == HistoryLogEntry.SourceType.USER:
            try:
                user = get_user_model().objects.get(id=obj["source_id"])
                return user.display_name
            except get_user_model().DoesNotExist:
                return None
        elif obj["source_type"] == HistoryLogEntry.SourceType.TELEGRAM:
            try:
                telegram = TelegramStored.objects.get(id=obj["source_id"])
                return telegram.telegram
            except TelegramStored.DoesNotExist:
                return None
        elif obj["source_type"] == HistoryLogEntry.SourceType.INGESTER:
            try:
                ingester = FileState.objects.get(id=obj["source_id"])
                return ingester.filename
            except FileState.DoesNotExist:
                return None
        return None
