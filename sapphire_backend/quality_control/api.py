from django.http import HttpRequest
from ninja import Query
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.utils.permissions import (
    regular_permissions,
)

from .models import HistoryLogEntry
from .schema import HistoryLogFilterSchema, HistoryLogOutputSchema


@api_controller(
    "quality-control/{organization_uuid}", tags=["Quality control"], auth=JWTAuth(), permissions=regular_permissions
)
class QualityControlAPIController:
    @route.get("history-logs", response=list[HistoryLogOutputSchema])
    def get_history_logs(self, request: HttpRequest, organization_uuid: str, filters: Query[HistoryLogFilterSchema]):
        history_logs = HistoryLogEntry.objects.all()
        return filters.filter(history_logs).order_by("created_date")
