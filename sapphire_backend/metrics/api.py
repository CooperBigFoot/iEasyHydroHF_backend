from typing import Any

from django.db.models import Avg, Count, Max, Min, Sum
from ninja import File, Query
from ninja.files import UploadedFile
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.utils.mixins.schemas import Message
from sapphire_backend.utils.permissions import (
    regular_permissions,
)

from .models import DischargeNorm, HydrologicalMetric, MeteorologicalMetric
from .schema import (
    DischargeNormOutputSchema,
    DischargeNormTypeFiltersSchema,
    HydrologicalMetricOutputSchema,
    HydroMetricFilterSchema,
    MeteoMetricFilterSchema,
    MeteorologicalMetricOutputSchema,
    MetricCountSchema,
    MetricTotalCountSchema,
    OrderQueryParamSchema,
    TimeBucketQueryParams,
)
from .timeseries.query import TimeseriesQueryManager

agg_func_mapping = {"avg": Avg, "count": Count, "min": Min, "max": Max, "sum": Sum}


@api_controller(
    "metrics/{organization_uuid}/hydro", tags=["Hydro Metrics"], auth=JWTAuth(), permissions=regular_permissions
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

    @route.get("metric-count", response={200: list[MetricCountSchema] | MetricTotalCountSchema})
    def get_hydro_metric_count(
        self, organization_uuid: str, filters: Query[HydroMetricFilterSchema], total_only: bool = False
    ):
        filter_dict = filters.dict(exclude_none=True)
        manager = TimeseriesQueryManager(
            model=HydrologicalMetric, organization_uuid=organization_uuid, filter_dict=filter_dict
        )

        if total_only:
            return {"total": manager.get_total()}
        else:
            return manager.get_metric_distribution()

    @route.get("time-bucket", response={200: list[dict[str, Any]], 400: Message})
    def time_bucket(
        self,
        organization_uuid: str,
        time_bucket: Query[TimeBucketQueryParams],
        order: Query[OrderQueryParamSchema],
        filters: Query[HydroMetricFilterSchema],
    ):
        filter_dict = filters.dict(exclude_none=True)
        time_bucket_dict = time_bucket.dict()
        time_bucket_dict["agg_func"] = time_bucket_dict["agg_func"].value
        order_param, order_direction = order.order_param, order.order_direction
        query_manager = TimeseriesQueryManager(
            model=HydrologicalMetric,
            organization_uuid=organization_uuid,
            filter_dict=filter_dict,
            order_param=order_param,
            order_direction=order_direction,
        )

        try:
            return query_manager.time_bucket(**time_bucket_dict)
        except ValueError as e:
            return 400, {"detail": str(e), "code": "time_bucket_error"}


@api_controller(
    "metrics/{organization_uuid}/meteo",
    tags=["Meteo Metrics"],
    auth=JWTAuth(),
    permissions=regular_permissions,
)
class MeteoMetricsAPIController:
    @route.get("", response={200: list[MeteorologicalMetricOutputSchema]})
    def get_meteo_metrics(
        self,
        organization_uuid: str,
        order: Query[OrderQueryParamSchema],
        filters: Query[MeteoMetricFilterSchema] = None,
    ):
        filter_dict = filters.dict(exclude_none=True)
        order_param, order_direction = order.order_param, order.order_direction
        return TimeseriesQueryManager(
            model=MeteorologicalMetric,
            organization_uuid=organization_uuid,
            order_param=order_param,
            order_direction=order_direction,
            filter_dict=filter_dict,
        ).execute_query()

    @route.get("metric-count", response={200: list[MetricCountSchema] | MetricTotalCountSchema})
    def get_meteo_metric_count(
        self, organization_uuid: str, filters: Query[MeteoMetricFilterSchema], total_only: bool = False
    ):
        filter_dict = filters.dict(exclude_none=True)
        manager = TimeseriesQueryManager(
            model=MeteorologicalMetric, organization_uuid=organization_uuid, filter_dict=filter_dict
        )

        if total_only:
            return {"total": manager.get_total()}
        else:
            return manager.get_metric_distribution()


@api_controller(
    "discharge_norms/{station_uuid}", tags=["Discharge norms"], auth=JWTAuth(), permissions=regular_permissions
)
class DischargeNormsAPIController:
    @route.get("", response=list[DischargeNormOutputSchema])
    def get_station_discharge_norm(self, station_uuid: str, norm_types: Query[DischargeNormTypeFiltersSchema]):
        return DischargeNorm.objects.filter(station=station_uuid, norm_type=norm_types.norm_type.value)

    @route.post("monthly", response={201: list[DischargeNormOutputSchema]})
    def upload_monthly_discharge_norm(self, station_uuid: str, file: UploadedFile = File(...)):
        pass

    @route.post("decadal", response={201: list[DischargeNormOutputSchema]})
    def upload_decadal_discharge_norm(self, station_uuid: str, file: UploadedFile = File(...)):
        pass
