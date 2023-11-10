from django.utils.translation import gettext_lazy as _
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
from sapphire_backend.stations.models import Sensor
from sapphire_backend.utils.permissions import (
    IsOrganizationMember,
    IsSuperAdmin,
    OrganizationExists,
    StationBelongsToOrganization,
)


@api_controller(
    "metrics/{organization_uuid}",
    tags=["Metrics"],
    auth=JWTAuth(),
    permissions=[OrganizationExists & (IsOrganizationMember | IsSuperAdmin)]  # & StationBelongsToOrganization],

)
class MetricsAPIController:
    @route.get("/stats")
    def get_metrics_stats(self, request, organization_uuid: str, ):
        stats = {}
        cnt_total_metrics = 0
        for metric in MetricParams:
            model_class = METRIC_MODEL_MAPPING[metric]
            cnt_metrics = model_class.objects.count()
            stats[f"cnt_{metric.value}"] = cnt_metrics
            cnt_total_metrics += cnt_metrics
        stats["cnt_total"] = cnt_total_metrics
        return stats

    @route.get("/{station_uuid}/latest", permissions=[StationBelongsToOrganization])
    def get_latest_metrics(self, request, organization_uuid: str, station_uuid: str, sensor_uuid: str | None):
        try:
            if sensor_uuid:
                sensor = Sensor.objects.for_station(station_uuid).get(uuid=sensor_uuid, is_active=True)
            else:
                sensor = Sensor.objects.for_station(station_uuid).get(is_default=True)
        except Sensor.DoesNotExist:
            return 404, {
                "detail": _("Station or sensor does not exist"),
                "code": "not_found",
            }
        print(sensor)

    @route.get("/{station_uuid}/timeseries/{metric}", permissions=[StationBelongsToOrganization],
               response={200: NinjaPaginationResponseSchema[TimeseriesOutputSchema]})
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
        base_qs = model_class.objects.filter(sensor__station=station_uuid)
        qs = filters.filter(base_qs)

        order_by = f"-{order_by.param.value}" if order_by.descending else order_by.param

        return qs.order_by(order_by)

    @route.get(
        "/{station_uuid}/timeseries/{metric}/group", permissions=[StationBelongsToOrganization],
        response={200: NinjaPaginationResponseSchema[TimeseriesGroupingOutputSchema]}
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
            model_class.objects.filter(sensor__station=station_uuid)
            .time_bucket(grouping_interval)
            .values("bucket", "unit")
            .annotate(value=aggregation_function)
        )

        ordering = "bucket" if ascending else "-bucket"
        qs = filters.filter(base_qs).order_by(ordering)
        return qs
