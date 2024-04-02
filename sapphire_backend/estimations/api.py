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
    def _run_query(
        self,
        view: str,
        organization_uuid: str,
        filters: dict,
        order_param: str,
        order_direction: str,
        limit: int = 100,
    ):
        manager = EstimationsViewQueryManager(
            model=view,
            organization_uuid=organization_uuid,
            filter_dict=filters,
            order_param=order_param,
            order_direction=order_direction,
        )

        return manager.execute_query(limit=limit)

    @route.get("water-level-daily-average", response={200: list[dict[str, Any]], 400: Message})
    def get_water_level_daily_average(
        self, organization_uuid: str, order: Query[OrderQueryParamSchema], filters: Query[EstimationsFilterSchema]
    ):
        return self._run_query(
            "estimations_water_level_daily_average",
            organization_uuid,
            filters.dict(exclude_none=True),
            order.order_param,
            order.order_direction,
        )

    @route.get("discharge-daily", response={200: list[dict[str, Any]], 400: Message})
    def get_water_discharge_daily(
        self, organization_uuid: str, order: Query[OrderQueryParamSchema], filters: Query[EstimationsFilterSchema]
    ):
        return self._run_query(
            "estimations_water_discharge_daily",
            organization_uuid,
            filters.dict(exclude_none=True),
            order.order_param,
            order.order_direction,
        )

    @route.get("discharge-daily-average", response={200: list[dict[str, Any]], 400: Message})
    def get_water_discharge_daily_average(
        self, organization_uuid: str, order: Query[OrderQueryParamSchema], filters: Query[EstimationsFilterSchema]
    ):
        return self._run_query(
            "estimations_water_discharge_daily_average",
            organization_uuid,
            filters.dict(exclude_none=True),
            order.order_param,
            order.order_direction,
        )

    @route.get("discharge-pentad-average", response={200: list[dict[str, Any]], 400: Message})
    def get_water_discharge_pentad_average(
        self, organization_uuid: str, order: Query[OrderQueryParamSchema], filters: Query[EstimationsFilterSchema]
    ):
        return self._run_query(
            "estimations_water_discharge_fiveday_average",
            organization_uuid,
            filters.dict(exclude_none=True),
            order.order_param,
            order.order_direction,
        )

    @route.get("discharge-decade-average", response={200: list[dict[str, Any]], 400: Message})
    def get_water_discharge_decade_average(
        self, organization_uuid: str, order: Query[OrderQueryParamSchema], filters: Query[EstimationsFilterSchema]
    ):
        return self._run_query(
            "estimations_water_discharge_decade_average",
            organization_uuid,
            filters.dict(exclude_none=True),
            order.order_param,
            order.order_direction,
        )
