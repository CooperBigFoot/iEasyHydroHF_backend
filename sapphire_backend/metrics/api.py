from ninja import Query
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.utils.permissions import (
    IsOrganizationMember,
    IsSuperAdmin,
    OrganizationExists,
)

from .models import HydrologicalMetric
from .schema import HydrologicalMetricFilterSchema, HydrologicalMetricOutputSchema, OrderQueryParams
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
        self, organization_uuid: str, order: Query[OrderQueryParams], filters: Query[HydrologicalMetricFilterSchema]
    ):
        return TimeseriesQueryManager(HydrologicalMetric, organization_uuid).execute_query()


@api_controller(
    "metrics/{organization_uuid}/meteo",
    tags=["meteo_metrics"],
    auth=JWTAuth(),
    permissions=[OrganizationExists & (IsOrganizationMember | IsSuperAdmin)],
)
class MeteoMetricsAPIController:
    pass
