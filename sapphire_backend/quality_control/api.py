from django.http import HttpRequest
from ninja import Query
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.metrics.models import HydrologicalMetric
from sapphire_backend.utils.permissions import (
    regular_permissions,
)

from .models import HistoryLogEntry
from .schema import HistoryLogFilterSchema, TimelineEntrySchema


@api_controller(
    "quality-control/{organization_uuid}", tags=["Quality control"], auth=JWTAuth(), permissions=regular_permissions
)
class QualityControlAPIController:
    @route.get("history-logs", response=list[TimelineEntrySchema])
    def get_history_logs(
        self,
        request: HttpRequest,
        organization_uuid: str,
        filters: Query[HistoryLogFilterSchema],
        include_current: bool = False,
        include_initial: bool = False,
    ):
        # Get history logs
        history_logs = HistoryLogEntry.objects.filter(**filters.dict(exclude_none=True)).order_by("created_date")

        # Transform logs into timeline entries
        timeline = []

        # Add initial state if requested and logs exist
        if include_initial and history_logs.exists():
            first_log = history_logs.first()
            timeline.append(
                {
                    "type": "initial",
                    "created_date": filters.timestamp_local,
                    "description": "",
                    "value": first_log.previous_value,
                    "value_code": first_log.previous_value_code,
                    "source_type": first_log.previous_source_type,
                    "source_id": first_log.previous_source_id,
                    "source_name": None,
                }
            )

        # Add all changes
        for log in history_logs:
            timeline.append(
                {
                    "type": "change",
                    "created_date": log.created_date,
                    "description": log.description,
                    "value": log.new_value,
                    "value_code": log.new_value_code,
                    "source_type": log.new_source_type,
                    "source_id": log.new_source_id,
                    "source_name": None,
                }
            )

        # Add current state if requested
        if include_current:
            try:
                current_metric = HydrologicalMetric.objects.get(**filters.dict(exclude_none=True))
                timeline.append(
                    {
                        "type": "current",
                        "created_date": None,
                        "description": "",
                        "value": current_metric.avg_value,
                        "value_code": current_metric.value_code,
                        "source_type": current_metric.source_type,
                        "source_id": current_metric.source_id,
                        "source_name": None,
                    }
                )
            except HydrologicalMetric.DoesNotExist:
                pass

        return timeline
