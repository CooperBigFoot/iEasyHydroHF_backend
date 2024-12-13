from datetime import datetime

from ninja import Field, Schema


class HistoryLogEntrySchema(Schema):
    created_date: datetime
    description: str
    value: float
    source_type: str = Field(..., alias="source_type.get_display_value")
    source_id: int
