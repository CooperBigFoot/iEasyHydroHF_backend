import os
from datetime import datetime as dt
from typing import Any

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db.models import Avg, Count, Max, Min, Sum
from django.http import FileResponse
from django.templatetags.static import static
from ninja import File, Query
from ninja.files import UploadedFile
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.estimations.query import EstimationsViewQueryManager
from sapphire_backend.stations.models import HydrologicalStation
from sapphire_backend.utils.datetime_helper import SmartDatetime
from sapphire_backend.utils.mixins.schemas import Message
from sapphire_backend.utils.permissions import (
    regular_permissions,
)

from .choices import HydrologicalMeasurementType, HydrologicalMetricName, MeteorologicalNormMetric, NormType
from .models import HydrologicalMetric, HydrologicalNorm, MeteorologicalMetric, MeteorologicalNorm
from .schema import (
    HydrologicalMetricOutputSchema,
    HydrologicalNormOutputSchema,
    HydrologicalNormTypeFiltersSchema,
    HydroMetricFilterSchema,
    MeteoMetricFilterSchema,
    MeteorologicalMetricOutputSchema,
    MeteorologicalNormOutputSchema,
    MeteorologicalNormTypeFiltersSchema,
    MetricCountSchema,
    MetricTotalCountSchema,
    OperationalJournalDailyDataSchema,
    OperationalJournalDecadalDataSchema,
    OperationalJournalDischargeDataSchema,
    OrderQueryParamSchema,
    TimeBucketQueryParams,
)
from .timeseries.query import TimeseriesQueryManager
from .utils.helpers import OperationalJournalDataTransformer
from .utils.parser import (
    DecadalDischargeNormFileParser,
    DecadalMeteoNormFileParser,
    MonthlyDischargeNormFileParser,
    MonthlyMeteoNormFileParser,
)

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
        filter_dict["station__site__organization"] = organization_uuid
        order_param, order_direction = order.order_param, order.order_direction
        return TimeseriesQueryManager(
            model=HydrologicalMetric,
            order_param=order_param,
            order_direction=order_direction,
            filter_dict=filter_dict,
        ).execute_query()

    @route.get("metric-count", response={200: list[MetricCountSchema] | MetricTotalCountSchema})
    def get_hydro_metric_count(
        self, organization_uuid: str, filters: Query[HydroMetricFilterSchema], total_only: bool = False
    ):
        filter_dict = filters.dict(exclude_none=True)
        filter_dict["station__site__organization"] = organization_uuid
        manager = TimeseriesQueryManager(model=HydrologicalMetric, filter_dict=filter_dict)

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
        filter_dict["station__site__organization"] = organization_uuid
        time_bucket_dict = time_bucket.dict()
        time_bucket_dict["agg_func"] = time_bucket_dict["agg_func"].value
        order_param, order_direction = order.order_param, order.order_direction
        query_manager = TimeseriesQueryManager(
            model=HydrologicalMetric,
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
        filter_dict["station__site__organization"] = organization_uuid
        order_param, order_direction = order.order_param, order.order_direction
        return TimeseriesQueryManager(
            model=MeteorologicalMetric,
            order_param=order_param,
            order_direction=order_direction,
            filter_dict=filter_dict,
        ).execute_query()

    @route.get("metric-count", response={200: list[MetricCountSchema] | MetricTotalCountSchema})
    def get_meteo_metric_count(
        self, organization_uuid: str, filters: Query[MeteoMetricFilterSchema], total_only: bool = False
    ):
        filter_dict = filters.dict(exclude_none=True)
        filter_dict["station__site__organization"] = organization_uuid
        manager = TimeseriesQueryManager(model=MeteorologicalMetric, filter_dict=filter_dict)

        if total_only:
            return {"total": manager.get_total()}
        else:
            return manager.get_metric_distribution()


@api_controller("hydrological-norms", tags=["Hydrological norms"], auth=JWTAuth())
class HydrologicalNormsAPIController:
    @route.get("download-template", response={200: None, 404: Message})
    def download_template_file(self, norm_type: Query[HydrologicalNormTypeFiltersSchema]):
        filename = (
            "discharge_norm_monthly_template.xlsx"
            if norm_type.norm_type.value == NormType.MONTHLY
            else "discharge_norm_decadal_template.xlsx"
        )
        file_path = static(f"templates/{filename}")
        absolute_path = os.path.join(settings.APPS_DIR, file_path.strip("/"))
        if os.path.exists(absolute_path):
            response = FileResponse(open(absolute_path, "rb"), as_attachment=True, filename=filename)
            return response
        else:
            return 404, {"detail": "Could not retrieve the file", "code": "file_not_found"}

    @route.get("{station_uuid}", response=list[HydrologicalNormOutputSchema], permissions=regular_permissions)
    def get_station_discharge_norm(self, station_uuid: str, norm_type: Query[HydrologicalNormTypeFiltersSchema]):
        return HydrologicalNorm.objects.for_station(station_uuid).filter(norm_type=norm_type.norm_type.value)

    @route.post("{station_uuid}", response={201: list[HydrologicalNormOutputSchema]}, permissions=regular_permissions)
    def upload_discharge_norm(
        self, station_uuid: str, norm_type: Query[HydrologicalNormTypeFiltersSchema], file: UploadedFile = File(...)
    ):
        parser_class = (
            DecadalDischargeNormFileParser
            if norm_type.norm_type == NormType.DECADAL
            else MonthlyDischargeNormFileParser
        )
        data = parser_class(file).parse()
        _ = HydrologicalNorm.objects.for_station(station_uuid).filter(norm_type=norm_type.norm_type.value).delete()

        norms = HydrologicalNorm.objects.bulk_create(
            [
                HydrologicalNorm(
                    station_id=station_uuid,
                    value=point["value"],
                    ordinal_number=point["ordinal_number"],
                    norm_type=norm_type.norm_type.value,
                )
                for point in data["discharge"]
            ]
        )

        return 201, norms


@api_controller("meteorological-norms", tags=["Meteorological norms"], auth=JWTAuth())
class MeteorologicalNormsAPIController:
    @route.get("download-template", response={200: None, 404: Message})
    def download_template_file(self, norm_types: Query[HydrologicalNormTypeFiltersSchema]):
        filename = (
            "meteo_norm_monthly_template.xlsx"
            if norm_types.norm_type.value == NormType.MONTHLY
            else "meteo_norm_decadal_template.xlsx"
        )
        file_path = static(f"templates/{filename}")
        absolute_path = os.path.join(settings.APPS_DIR, file_path.strip("/"))
        if os.path.exists(absolute_path):
            response = FileResponse(open(absolute_path, "rb"), as_attachment=True, filename=filename)
            return response
        else:
            return 404, {"detail": "Could not retrieve the file", "code": "file_not_found"}

    @route.get("{station_uuid}", response=list[MeteorologicalNormOutputSchema], permissions=regular_permissions)
    def get_station_meteorological_norm(
        self, station_uuid: str, norm_filters: Query[MeteorologicalNormTypeFiltersSchema]
    ):
        return MeteorologicalNorm.objects.for_station(station_uuid).filter(
            norm_type=norm_filters.norm_type.value, norm_metric=norm_filters.norm_metric.value
        )

    @route.post(
        "{station_uuid}",
        response={201: dict[str, list[MeteorologicalNormOutputSchema]]},
        permissions=regular_permissions,
    )
    def upload_meteorological_norm(
        self, station_uuid: str, norm_type: Query[HydrologicalNormTypeFiltersSchema], file: UploadedFile = File(...)
    ):
        parser_class = (
            DecadalMeteoNormFileParser if norm_type.norm_type == NormType.DECADAL else MonthlyMeteoNormFileParser
        )
        data = parser_class(file).parse()
        _ = MeteorologicalNorm.objects.for_station(station_uuid).filter(norm_type=norm_type.norm_type.value).delete()

        precipitation_norms = MeteorologicalNorm.objects.bulk_create(
            [
                MeteorologicalNorm(
                    station_id=station_uuid,
                    value=point["value"],
                    ordinal_number=point["ordinal_number"],
                    norm_type=norm_type.norm_type.value,
                    norm_metric=MeteorologicalNormMetric.PRECIPITATION,
                )
                for point in data["precipitation"]
            ]
        )
        temperature_norms = MeteorologicalNorm.objects.bulk_create(
            [
                MeteorologicalNorm(
                    station_id=station_uuid,
                    value=point["value"],
                    ordinal_number=point["ordinal_number"],
                    norm_type=norm_type.norm_type.value,
                    norm_metric=MeteorologicalNormMetric.TEMPERATURE,
                )
                for point in data["temperature"]
            ]
        )

        return 201, {"precipitation": precipitation_norms, "temperature": temperature_norms}


@api_controller(
    "metrics/operational-journal/{station_uuid}/{year}/{month}",
    tags=["Operational journal"],
    auth=JWTAuth(),
    permissions=regular_permissions,
)
class OperationalJournalAPIController:
    @route.get("daily-data", response={200: list[OperationalJournalDailyDataSchema]})
    def get_daily_data(self, station_uuid: str, year: int, month: int):
        station = HydrologicalStation.objects.get(uuid=station_uuid)
        first_day_current_month = dt(year, month, 1)
        last_day_previous_month = first_day_current_month - relativedelta(days=1)
        first_day_next_month = first_day_current_month + relativedelta(months=1)
        dt_start = SmartDatetime(last_day_previous_month, station).day_beginning_local.isoformat()
        dt_end = SmartDatetime(first_day_next_month, station).day_beginning_local.isoformat()
        common_filter_dict = {"timestamp_local__gte": dt_start, "timestamp_local__lt": dt_end}
        estimations_filter_dict = {"station_id": station.id, **common_filter_dict}
        daily_data_filter_dict = {
            **common_filter_dict,
            "station": station.id,
            "value_type__in": [HydrologicalMeasurementType.MANUAL.value],
            "metric_name__in": [
                HydrologicalMetricName.WATER_LEVEL_DAILY.value,
                HydrologicalMetricName.PRECIPITATION_DAILY.value,
                HydrologicalMetricName.WATER_TEMPERATURE.value,
                HydrologicalMetricName.AIR_TEMPERATURE.value,
                HydrologicalMetricName.ICE_PHENOMENA_OBSERVATION.value,
            ],
        }

        operational_journal_data = []

        daily_hydro_metric_data = TimeseriesQueryManager(
            model=HydrologicalMetric,
            order_param="timestamp_local",
            order_direction="ASC",
            filter_dict=daily_data_filter_dict,
        ).execute_query()

        operational_journal_data.extend(
            daily_hydro_metric_data.values("timestamp_local", "avg_value", "metric_name", "value_code")
        )

        estimated_data_queries = [
            ("estimations_water_discharge_daily", HydrologicalMetricName.WATER_DISCHARGE_DAILY),
            ("estimations_water_level_daily_average", HydrologicalMetricName.WATER_LEVEL_DAILY_AVERAGE),
            ("estimations_water_discharge_daily_average", HydrologicalMetricName.WATER_DISCHARGE_DAILY_AVERAGE),
        ]

        for view_name, metric_name in estimated_data_queries:
            estimation_data = EstimationsViewQueryManager(
                view_name, order_param="timestamp_local", order_direction="ASC", filter_dict=estimations_filter_dict
            ).execute_query()

            operational_journal_data.extend({**d, "metric_name": metric_name} for d in estimation_data)

        prepared_data = OperationalJournalDataTransformer(operational_journal_data).get_daily_data()

        return prepared_data

    @route.get("discharge-data", response=list[OperationalJournalDischargeDataSchema])
    def get_discharge_data(self, station_uuid: str, year: int, month: int):
        station = HydrologicalStation.objects.get(uuid=station_uuid)
        first_day_current_month = dt(year, month, 1)
        dt_start = SmartDatetime(first_day_current_month, station).day_beginning_local.isoformat()
        first_day_next_month = first_day_current_month + relativedelta(months=1)
        dt_end = SmartDatetime(first_day_next_month, station).day_beginning_local.isoformat()

        discharge_data = TimeseriesQueryManager(
            model=HydrologicalMetric,
            order_param="timestamp_local",
            order_direction="ASC",
            filter_dict={
                "timestamp_local__gte": dt_start,
                "timestamp_local__lt": dt_end,
                "station": station.id,
                "value_type__in": [HydrologicalMeasurementType.MANUAL.value],
                "metric_name__in": [
                    HydrologicalMetricName.WATER_LEVEL_DECADAL,
                    HydrologicalMetricName.WATER_DISCHARGE_DAILY,
                    HydrologicalMetricName.RIVER_CROSS_SECTION_AREA,
                ],
            },
        ).execute_query()

        prepared_data = OperationalJournalDataTransformer(
            discharge_data.values("timestamp_local", "avg_value", "metric_name")
        ).get_discharge_data()

        return prepared_data

    @route.get("decadal-data", response=list[OperationalJournalDecadalDataSchema])
    def get_decadal_data(self, station_uuid: str, year: int, month: int):
        station = HydrologicalStation.objects.get(uuid=station_uuid)
        first_day_current_month = dt(year, month, 1)
        dt_start = SmartDatetime(first_day_current_month, station).day_beginning_local.isoformat()
        first_day_next_month = first_day_current_month + relativedelta(months=1)
        dt_end = SmartDatetime(first_day_next_month, station).day_beginning_local.isoformat()

        decadal_data = []

        querying_views = [
            ("estimations_water_level_decade_average", HydrologicalMetricName.WATER_LEVEL_DECADE_AVERAGE),
            ("estimations_water_discharge_decade_average", HydrologicalMetricName.WATER_DISCHARGE_DECADE_AVERAGE),
        ]

        for view_name, metric_name in querying_views:
            view_data = EstimationsViewQueryManager(
                view_name,
                order_param="timestamp_local",
                order_direction="ASC",
                filter_dict={
                    "timestamp_local__gte": dt_start,
                    "timestamp_local__lt": dt_end,
                    "station_id": station.id,
                },
            ).execute_query()

            decadal_data.extend({**d, "metric_name": metric_name} for d in view_data)

        prepared_data = OperationalJournalDataTransformer(decadal_data).get_decadal_data()

        return prepared_data
