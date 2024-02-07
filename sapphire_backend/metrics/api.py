from ninja import Query
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.utils.permissions import (
    IsOrganizationMember,
    IsSuperAdmin,
    OrganizationExists,
)

from .models import HydrologicalMetric
from .schema import (
    HydrologicalMetricOutputSchema,
    HydroMetricFilterSchema,
    OrderQueryParamSchema,
)
from .timeseries.query import TimeseriesQueryManager


@api_controller(
    "metrics/{organization_uuid}/hydro",
    tags=["Hydro Metrics"],
    auth=JWTAuth(),
    permissions=[OrganizationExists & (IsOrganizationMember | IsSuperAdmin)],
)
class HydroMetricsAPIController:
    @route.get("", response={200: list[HydrologicalMetricOutputSchema]})
    def get_hydro_metrics(
        self,
        organization_uuid: str,
        order: Query[OrderQueryParamSchema],
        filters: Query[HydroMetricFilterSchema] = None,
    ):
        filter_dict = filters.dict(exclude_none=True)
        order_param, order_direction = order.order_param, order.order_direction
        return TimeseriesQueryManager(
            model=HydrologicalMetric,
            organization_uuid=organization_uuid,
            order_param=order_param,
            order_direction=order_direction,
            filter_dict=filter_dict,
        ).execute_query()


@api_controller(
    "metrics/{organization_uuid}/meteo",
    tags=["meteo_metrics"],
    auth=JWTAuth(),
    permissions=[OrganizationExists & (IsOrganizationMember | IsSuperAdmin)],
)
class MeteoMetricsAPIController:
    pass
