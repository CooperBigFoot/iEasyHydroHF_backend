from ninja import Query
from ninja_extra import api_controller, route
from ninja_extra.pagination import LimitOffsetPagination, paginate
from ninja_extra.schemas import NinjaPaginationResponseSchema
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.metrics.schema import (
    AggregationFunctionParams,
    MetricParams,
    OrderQueryParams,
    TimeseriesFiltersSchema,
    TimeseriesGroupingOutputSchema,
    TimeseriesOutputSchema,
)
from sapphire_backend.metrics.utils.helpers import AGGREGATION_MAPPING, METRIC_MODEL_MAPPING
from sapphire_backend.utils.permissions import (
    HydroStationBelongsToOrganization,
    IsOrganizationMember,
    IsSuperAdmin,
    OrganizationExists,
)


@api_controller(
    "metrics/{organization_uuid}",
    tags=["Metrics"],
    auth=JWTAuth(),
    permissions=[OrganizationExists & (IsOrganizationMember | IsSuperAdmin)],
)
class MetricsAPIController:
    @route.get("/stats")
    def get_metrics_stats(
        self,
        request,
        organization_uuid: str,
    ):
        stats = {}
        cnt_total_metrics = 0
        for metric in MetricParams:
            model_class = METRIC_MODEL_MAPPING[metric]
            cnt_metrics = model_class.objects.filter(hydro_station__site__organization=organization_uuid).count()
            stats[f"cnt_{metric.value}"] = cnt_metrics
            cnt_total_metrics += cnt_metrics
        stats["cnt_total"] = cnt_total_metrics
        return stats

    @route.get("/{station_uuid}/latest", permissions=[HydroStationBelongsToOrganization])
    def get_latest_metrics(self, request, organization_uuid: str, station_uuid: str, sensor_id: str | None):
        pass

    @route.get(
        "/{station_uuid}/timeseries/{metric}",
        permissions=[HydroStationBelongsToOrganization],
        response={200: NinjaPaginationResponseSchema[TimeseriesOutputSchema]},
    )
    @paginate(LimitOffsetPagination, page_size=100)
    def get_timeseries(
        self,
        request,
        organization_uuid: str,
        station_uuid: str,
        metric: MetricParams,
        filters: TimeseriesFiltersSchema = Query(...),
        order_by: OrderQueryParams = Query(...),
    ):
        model_class = METRIC_MODEL_MAPPING[metric]
        base_qs = model_class.objects.filter(hydro_station=station_uuid)
        qs = filters.filter(base_qs)

        order_by = f"-{order_by.param.value}" if order_by.descending else order_by.param

        return qs.order_by(order_by)

    @route.get(
        "/{station_uuid}/timeseries/{metric}/group",
        permissions=[HydroStationBelongsToOrganization],
        response={200: NinjaPaginationResponseSchema[TimeseriesGroupingOutputSchema]},
    )
    @paginate(LimitOffsetPagination)
    def get_grouped_timeseries(
        self,
        request,
        organization_uuid: str,
        station_uuid: str,
        metric: MetricParams,
        grouping_interval: str,
        grouping_function: AggregationFunctionParams = Query(...),
        filters: TimeseriesFiltersSchema = Query(...),
        ascending: bool = True,
    ):
        model_class = METRIC_MODEL_MAPPING[metric]
        aggregation_function = AGGREGATION_MAPPING[grouping_function]
        base_qs = (
            model_class.objects.filter(hydro_station=station_uuid)
            .time_bucket(grouping_interval)
            .values("bucket", "unit")
            .annotate(value=aggregation_function)
        )

        ordering = "bucket" if ascending else "-bucket"
        qs = filters.filter(base_qs).order_by(ordering)
        return qs
