import os
from typing import Any

from django.conf import settings
from django.db.models import Avg, Count, Max, Min, Sum
from django.http import FileResponse
from django.templatetags.static import static
from ninja import File, Query
from ninja.files import UploadedFile
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.utils.mixins.schemas import Message
from sapphire_backend.utils.permissions import (
    regular_permissions,
)

from .choices import NormType
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
from .utils.parser import DecadalDischargeNormFileParser, MonthlyDischargeNormFileParser

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


@api_controller("discharge-norms", tags=["Discharge norms"], auth=JWTAuth())
class DischargeNormsAPIController:
    @route.get("download-template", response={200: None, 404: Message})
    def download_template_file(self, norm_types: Query[DischargeNormTypeFiltersSchema]):
        filename = (
            "discharge_norm_monthly_template.xlsx"
            if norm_types.norm_type.value == NormType.MONTHLY
            else "discharge_norm_decadal_template.xlsx"
        )
        file_path = static(f"templates/{filename}")
        absolute_path = os.path.join(settings.APPS_DIR, file_path.strip("/"))
        if os.path.exists(absolute_path):
            response = FileResponse(open(absolute_path, "rb"), as_attachment=True, filename=filename)
            return response
        else:
            return 404, {"detail": "Could not retrieve the file", "code": "file_not_found"}

    @route.get("{station_uuid}", response=list[DischargeNormOutputSchema], permissions=regular_permissions)
    def get_station_discharge_norm(self, station_uuid: str, norm_types: Query[DischargeNormTypeFiltersSchema]):
        return DischargeNorm.objects.for_station(station_uuid).filter(norm_type=norm_types.norm_type.value)

    @route.post(
        "{station_uuid}/monthly", response={201: list[DischargeNormOutputSchema]}, permissions=regular_permissions
    )
    def upload_monthly_discharge_norm(self, station_uuid: str, file: UploadedFile = File(...)):
        parser = MonthlyDischargeNormFileParser(file)

        data = parser.parse()

        # first delete the existing records
        _ = DischargeNorm.objects.filter(station=station_uuid, norm_type=NormType.MONTHLY).delete()

        # will not call the .save method, thus the pre_save and post_save signals won't be emitted
        norms = DischargeNorm.objects.bulk_create(
            [
                DischargeNorm(
                    station_id=station_uuid,
                    value=point["value"],
                    ordinal_number=point["ordinal_number"],
                    norm_type=NormType.MONTHLY,
                )
                for point in data["discharge"]
            ]
        )

        return 201, norms

    @route.post(
        "{station_uuid}/decadal", response={201: list[DischargeNormOutputSchema]}, permissions=regular_permissions
    )
    def upload_decadal_discharge_norm(self, station_uuid: str, file: UploadedFile = File(...)):
        parser = DecadalDischargeNormFileParser(file)

        data = parser.parse()

        # first delete the existing records
        _ = DischargeNorm.objects.filter(station=station_uuid, norm_type=NormType.DECADAL).delete()

        # will not call the .save method, thus the pre_save and post_save signals won't be emitted
        norms = DischargeNorm.objects.bulk_create(
            [
                DischargeNorm(
                    station_id=station_uuid,
                    value=point["value"],
                    ordinal_number=point["ordinal_number"],
                    norm_type=NormType.DECADAL,
                )
                for point in data["discharge"]
            ]
        )

        return 201, norms


@api_controller(
    "metrics/operational-journal/{station_uuid}/{year}/{month}",
    tags=["Operational journal"],
    auth=JWTAuth(),
    permissions=regular_permissions,
)
class OperationalJournalAPIController:
    @route.get("daily-data")
    def get_daily_data(self, station_uuid: str, year: int, month: int):
        pass

    @route.get("discharge-data")
    def get_discharge_data(self, station_uuid: str, year: int, month: int):
        pass

    @route.get("decadal-data")
    def get_decadal_data(self, station_uuid: str, year: int, month: int):
        pass
