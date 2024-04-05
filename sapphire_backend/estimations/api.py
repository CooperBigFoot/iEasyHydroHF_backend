from typing import Any

from ninja import Query
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.utils.mixins.schemas import Message
from sapphire_backend.utils.permissions import (
    regular_permissions,
)

from .query import EstimationsViewQueryManager
from .schema import EstimationsFilterSchema, OrderQueryParamSchema


@api_controller(
    "estimations/{organization_uuid}", tags=["Estimations"], auth=JWTAuth(), permissions=regular_permissions
)
class EstimationsAPIController:
    @route.get("discharge-daily-average", response={200: list[dict[str, Any]], 400: Message})
    def get_water_discharge_daily_average(
        self,
        organization_uuid: str,
        order: Query[OrderQueryParamSchema],
        filters: Query[EstimationsFilterSchema],
        limit: int | None = 365,
    ):
        return EstimationsViewQueryManager(
            "estimations_water_discharge_daily_average",
            organization_uuid,
            filters.dict(exclude_none=True),
            order.order_param,
            order.order_direction,
        ).execute_query(limit)
