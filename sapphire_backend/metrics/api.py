import io
import math
import os
from collections import defaultdict
from datetime import datetime as dt
from typing import Any

import pandas as pd
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Avg, Case, Count, DecimalField, Max, Min, QuerySet, Sum, Value, When
from django.db.models.functions import Round
from django.http import FileResponse
from django.templatetags.static import static
from ninja import File, Query
from ninja.errors import ValidationError
from ninja.files import UploadedFile
from ninja_extra import api_controller, route
from ninja_extra.pagination import PageNumberPaginationExtra, paginate
from ninja_jwt.authentication import JWTAuth
from zoneinfo import ZoneInfo

from sapphire_backend.stations.models import HydrologicalStation, MeteorologicalStation, VirtualStation
from sapphire_backend.utils.datetime_helper import SmartDatetime
from sapphire_backend.utils.mixins.models import SourceTypeMixin
from sapphire_backend.utils.mixins.schemas import Message
from sapphire_backend.utils.permissions import (
    regular_permissions,
)
from sapphire_backend.utils.rounding import custom_ceil, hydrological_round

from ..estimations.models import (
    EstimationsAirTemperatureDaily,
    EstimationsWaterDischargeDaily,
    EstimationsWaterDischargeDailyAverage,
    EstimationsWaterDischargeDailyAverageVirtual,
    EstimationsWaterDischargeDailyVirtual,
    EstimationsWaterDischargeDecadeAverage,
    EstimationsWaterDischargeDecadeAverageVirtual,
    EstimationsWaterLevelDailyAverage,
    EstimationsWaterLevelDecadeAverage,
    EstimationsWaterTemperatureDaily,
    HydrologicalNormVirtual,
)
from .choices import (
    HydrologicalMeasurementType,
    HydrologicalMetricName,
    MeteorologicalMeasurementType,
    MeteorologicalMetricName,
    MeteorologicalNormMetric,
    MetricUnit,
    NormType,
)
from .models import HydrologicalMetric, HydrologicalNorm, MeteorologicalMetric, MeteorologicalNorm
from .schema import (
    BulkDataDownloadInputSchema,
    DetailedDailyHydroMetricFilterSchema,
    DetailedDailyHydroMetricSchema,
    DisplayType,
    HFChartSchema,
    HydrologicalMetricOutputSchema,
    HydrologicalNormOutputSchema,
    HydrologicalNormTypeFiltersSchema,
    HydroMetricFilterSchema,
    MeasuredDischargeMeasurementSchema,
    MeteoMetricFilterSchema,
    MeteorologicalManualInputSchema,
    MeteorologicalMetricOutputSchema,
    MeteorologicalNormOutputSchema,
    MeteorologicalNormTypeFiltersSchema,
    MetricCountSchema,
    MetricDisplayTypeSchema,
    MetricTotalCountSchema,
    MetricViewTypeSchema,
    OperationalJournalDailyDataSchema,
    OperationalJournalDailyVirtualDataSchema,
    OperationalJournalDecadalHydroDataSchema,
    OperationalJournalDecadalHydroVirtualDataSchema,
    OperationalJournalDecadalMeteoDataSchema,
    OperationalJournalDischargeDataSchema,
    OrderQueryParamSchema,
    TimeBucketQueryParams,
    TimestampGroupedHydroMetricSchema,
    UpdateHydrologicalMetricResponseSchema,
    UpdateHydrologicalMetricSchema,
    ViewType,
)
from .timeseries.query import TimeseriesQueryManager
from .utils.bulk_data import (
    write_bulk_data_hydro_auto_sheets,
    write_bulk_data_hydro_manual_sheets,
    write_bulk_data_meteo_sheets,
    write_bulk_data_virtual_sheets,
)
from .utils.helpers import (
    HydrologicalYearResolver,
    OperationalJournalDataTransformer,
    OperationalJournalVirtualDataTransformer,
    create_norm_dataframe,
    hydro_station_uuids_belong_to_organization_uuid,
    meteo_station_uuids_belong_to_organization_uuid,
    save_metric_and_create_log,
    virtual_station_uuids_belong_to_organization_uuid,
)
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
    @staticmethod
    def _validate_datetime_range(filter_dict, allowed_days: int = 30):
        start = filter_dict.get("timestamp_local__gte") or filter_dict.get("timestamp_local__gt")
        end = filter_dict.get("timestamp_local__lt") or filter_dict.get("timestamp_local__lte")

        date_range = end - start

        if date_range.days > allowed_days:
            raise ValidationError("Date range cannot be more than 30 days")

    def _get_queryset(
        self,
        view_type: str,
        filter_dict: dict,
        order_param: str,
        order_direction: str,
    ) -> QuerySet:
        """Get the appropriate queryset based on view type and display type."""

        if view_type == ViewType.MEASUREMENTS:
            self._validate_datetime_range(filter_dict, allowed_days=30)  # 30 days for raw data
        else:  # ViewType.DAILY
            self._validate_datetime_range(filter_dict, allowed_days=365)  # 365 days for daily data

        # For chart views, only return water level data
        if view_type == "daily":
            model_mapping = {
                HydrologicalMetricName.WATER_LEVEL_DAILY_AVERAGE: EstimationsWaterLevelDailyAverage,
                HydrologicalMetricName.WATER_DISCHARGE_DAILY: EstimationsWaterDischargeDaily,
                HydrologicalMetricName.WATER_DISCHARGE_DAILY_AVERAGE: EstimationsWaterDischargeDailyAverage,
                HydrologicalMetricName.WATER_TEMPERATURE_DAILY_AVERAGE: EstimationsWaterTemperatureDaily,
                HydrologicalMetricName.AIR_TEMPERATURE_DAILY_AVERAGE: EstimationsAirTemperatureDaily,
            }

            metric_names = filter_dict.get("metric_name__in", [])
            if not metric_names:
                raise ValidationError("metric_name__in is required for daily view")

            queries = [
                model_mapping[metric].objects.filter(**filter_dict)
                for metric in metric_names
                if metric in model_mapping
            ]

            if not queries:
                raise ValueError("No valid metrics requested for daily view")

            qs = queries[0].union(*queries[1:]) if len(queries) > 1 else queries[0]
            return qs.order_by(f"{'-' if order_direction.lower() == 'desc' else ''}{order_param}")

        # For raw/grouped views
        return HydrologicalMetric.objects.filter(**filter_dict).order_by(
            f"{'-' if order_direction.lower() == 'desc' else ''}{order_param}"
        )

    def _prepare_annotations(self, filter_dict: dict) -> dict:
        """Prepare annotations for grouped views."""
        return {
            metric: Max(
                Case(
                    When(metric_name=metric, then=Round("avg_value", precision=1)),
                    default=Value(None),
                    output_field=DecimalField(),
                )
            )
            for metric in filter_dict.get("metric_name__in", [])
        }

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

    @route.get("{station_uuid}/measured-discharge", response={200: list[MeasuredDischargeMeasurementSchema]})
    def get_measured_discharge_points(self, organization_uuid: str, station_uuid: str, year: int):
        station = HydrologicalStation.objects.select_related("site__organization").get(uuid=station_uuid)
        organization = station.site.organization
        year_resolver = HydrologicalYearResolver(organization, year)
        filter_dict = {
            "station": station.id,
            "timestamp_local__gte": year_resolver.get_start_date(),
            "timestamp_local__lt": year_resolver.get_end_date(),
            "metric_name__in": [
                HydrologicalMetricName.WATER_LEVEL_DECADAL,
                HydrologicalMetricName.WATER_DISCHARGE_DAILY,
                HydrologicalMetricName.RIVER_CROSS_SECTION_AREA,
            ],
            "value_type": HydrologicalMeasurementType.MANUAL,
        }
        measurements = TimeseriesQueryManager(model=HydrologicalMetric, filter_dict=filter_dict).execute_query()

        grouped_data = defaultdict(dict)

        for entry in measurements:
            grouped_data[entry.timestamp_local][entry.metric_name] = entry.avg_value
        ret = [
            {
                "date": str(date),
                "h": custom_ceil(values.get("WLDC")),
                "q": hydrological_round(values.get("WDD")),
                "f": hydrological_round(values.get("RCSA")),
            }
            for date, values in grouped_data.items()
        ]
        return ret

    @route.get("{view_type}/chart")
    def get_hydro_metrics_chart(
        self,
        organization_uuid: str,
        view_type: MetricViewTypeSchema,
        filters: Query[HydroMetricFilterSchema] = None,
    ):
        filter_dict = filters.dict(exclude_none=True)
        filter_dict["station__site__organization"] = organization_uuid

        qs = self._get_queryset(
            view_type=view_type.view_type,
            filter_dict=filter_dict,
            order_param="timestamp_local",
            order_direction="ASC",
        )

        if view_type.view_type == ViewType.DAILY:
            results = defaultdict(dict)
            for record in qs:
                results[record.timestamp_local][record.metric_name] = record.avg_value
            return [HFChartSchema(timestamp_local=ts, **values) for ts, values in results.items()]
        else:
            annotations = self._prepare_annotations(filter_dict)
            return [
                HFChartSchema(
                    timestamp_local=record["timestamp_local"],
                    **{k: v for k, v in record.items() if k != "timestamp_local"},
                )
                for record in qs.values("timestamp_local").annotate(**annotations)
            ]

    @route.get("{view_type}/{display_type}")
    @paginate(PageNumberPaginationExtra, page_size=100, max_page_size=101)
    def get_hydro_metrics(
        self,
        organization_uuid: str,
        view_type: MetricViewTypeSchema,
        display_type: MetricDisplayTypeSchema,
        order: Query[OrderQueryParamSchema],
        filters: Query[HydroMetricFilterSchema] = None,
    ):
        filter_dict = filters.dict(exclude_none=True)
        filter_dict["station__site__organization"] = organization_uuid

        qs = self._get_queryset(
            view_type=view_type.view_type,
            filter_dict=filter_dict,
            order_param=order.order_param,
            order_direction=order.order_direction,
        )

        if display_type.display_type == DisplayType.GROUPED:
            return [
                TimestampGroupedHydroMetricSchema(
                    timestamp_local=record["timestamp_local"],
                    **{k: v for k, v in record.items() if k != "timestamp_local"},
                )
                for record in qs.values("timestamp_local").annotate(**self._prepare_annotations(filter_dict))
            ]
        else:  # raw or daily
            return [HydrologicalMetricOutputSchema(**record) for record in qs.values()]

    @route.get("detailed-daily", response={200: list[DetailedDailyHydroMetricSchema]})
    def get_detailed_daily_hydro_metrics(
        self,
        organization_uuid: str,
        filters: Query[DetailedDailyHydroMetricFilterSchema],
    ):
        """Get detailed daily hydro metrics including specific time measurements."""
        filter_dict = filters.dict(exclude_none=True)

        filter_dict["station__site__organization"] = organization_uuid
        # Get temperature data if requested
        requested_metrics = filter_dict.get("metric_name__in", [])
        temp_data = {}

        if HydrologicalMetricName.AIR_TEMPERATURE_DAILY_AVERAGE in requested_metrics:
            air_temp_data = EstimationsAirTemperatureDaily.objects.filter(
                station_id=filter_dict["station"],
                timestamp_local__range=(
                    filter_dict.get("timestamp_local__gte"),
                    filter_dict.get("timestamp_local__lt"),
                ),
            ).values("timestamp_local", "avg_value")
            temp_data["air_temp"] = {d["timestamp_local"].date(): d["avg_value"] for d in air_temp_data}

        if HydrologicalMetricName.WATER_TEMPERATURE_DAILY_AVERAGE in requested_metrics:
            water_temp_data = EstimationsWaterTemperatureDaily.objects.filter(
                station_id=filter_dict["station"],
                timestamp_local__range=(
                    filter_dict.get("timestamp_local__gte"),
                    filter_dict.get("timestamp_local__lt"),
                ),
            ).values("timestamp_local", "avg_value")
            temp_data["water_temp"] = {d["timestamp_local"].date(): d["avg_value"] for d in water_temp_data}

        # Get water level data
        water_level_manager = TimeseriesQueryManager(
            model=HydrologicalMetric,
            filter_dict={
                **filter_dict,
            },
        )

        water_level_data = water_level_manager.get_detailed_daily_metrics()

        # Combine all data
        results = []
        for day_data in water_level_data:
            date = day_data["date"].date()
            results.append(
                DetailedDailyHydroMetricSchema(
                    **day_data,
                    id=day_data["date"],
                    daily_average_air_temperature=temp_data.get("air_temp", {}).get(date),
                    daily_average_water_temperature=temp_data.get("water_temp", {}).get(date),
                )
            )
        return results

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

    @route.put("update", response={200: UpdateHydrologicalMetricResponseSchema, 404: Message, 400: Message})
    def update_hydrological_metric(self, request, payload: UpdateHydrologicalMetricSchema) -> dict:
        try:
            with transaction.atomic():
                # Find the existing metric using composite key fields
                metric = HydrologicalMetric(
                    timestamp_local=payload.timestamp_local,
                    station_id=payload.station_id,
                    metric_name=payload.metric_name,
                    value_type=payload.value_type,
                    sensor_identifier=payload.sensor_identifier,
                    avg_value=payload.new_value,
                    value_code=payload.value_code,
                    source_type=SourceTypeMixin.SourceType.USER,
                    source_id=request.user.id,
                )

                save_metric_and_create_log(metric, description=payload.comment)

                return {"success": True, "message": "Metric updated successfully"}

        except HydrologicalMetric.DoesNotExist:
            raise ValidationError("Metric not found")
        except Exception as e:
            raise ValidationError(f"Failed to update metric: {str(e)}")


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
        limit: int | None = 365,
    ):
        filter_dict = filters.dict(exclude_none=True)
        filter_dict["station__site__organization"] = organization_uuid
        order_param, order_direction = order.order_param, order.order_direction
        return TimeseriesQueryManager(
            model=MeteorologicalMetric,
            order_param=order_param,
            order_direction=order_direction,
            filter_dict=filter_dict,
        ).execute_query()[:limit]

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

    @route.post("{station_uuid}/manual-input", response={201: list[MeteorologicalMetricOutputSchema]})
    def save_decadal_meteo_data(
        self, organization_uuid: str, station_uuid: str, meteo_data: MeteorologicalManualInputSchema
    ):
        meteo_station = MeteorologicalStation.objects.get(uuid=station_uuid)
        decade_to_day_mapping = {1: 5, 2: 15, 3: 25, 4: 15}
        ts = dt(
            year=meteo_data.year,
            month=meteo_data.month,
            day=decade_to_day_mapping[meteo_data.decade],
            hour=12,
            tzinfo=ZoneInfo("UTC"),
        )
        precipitation_metric = MeteorologicalMetric(
            timestamp_local=ts,
            value=meteo_data.precipitation,
            metric_name=MeteorologicalMetricName.PRECIPITATION_MONTH_AVERAGE
            if meteo_data.decade == 4
            else MeteorologicalMetricName.PRECIPITATION_DECADE_AVERAGE,
            station=meteo_station,
            value_type=MeteorologicalMeasurementType.MANUAL,
            unit=MetricUnit.PRECIPITATION,
        )
        precipitation_metric.save()
        air_temperature_metric = MeteorologicalMetric(
            value=meteo_data.temperature,
            timestamp_local=ts,
            metric_name=MeteorologicalMetricName.AIR_TEMPERATURE_MONTH_AVERAGE
            if meteo_data.decade == 4
            else MeteorologicalMetricName.AIR_TEMPERATURE_DECADE_AVERAGE,
            station=meteo_station,
            value_type=MeteorologicalMeasurementType.MANUAL,
            unit=MetricUnit.TEMPERATURE,
        )
        air_temperature_metric.save()

        return 201, [precipitation_metric, air_temperature_metric]


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
    def get_station_discharge_norm(
        self, station_uuid: str, norm_type: Query[HydrologicalNormTypeFiltersSchema], virtual: bool = False
    ):
        if virtual:
            return HydrologicalNormVirtual.objects.filter(station=station_uuid, norm_type=norm_type.norm_type.value)
        else:
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
                if not math.isnan(point["value"])
            ]
        )

        return 201, norms

    @route.get("{station_uuid}/download", response={200: None, 404: Message})
    def download_discharge_norm(self, station_uuid: str, norm_type: Query[HydrologicalNormTypeFiltersSchema]):
        station = HydrologicalStation.objects.get(uuid=station_uuid)
        norm_data = HydrologicalNorm.objects.for_station(station_uuid).filter(norm_type=norm_type.norm_type.value)
        output_df = create_norm_dataframe(norm_data, norm_type.norm_type)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            output_df.to_excel(writer, index=False, sheet_name="discharge")

        output_filename = f"historic-data-discharge-{station.station_code}.xlsx"
        buffer.seek(0)
        response = FileResponse(buffer, as_attachment=True, filename=output_filename)

        return response


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
                if not math.isnan(point["value"])
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
                if not math.isnan(point["value"])
            ]
        )

        return 201, {"precipitation": precipitation_norms, "temperature": temperature_norms}

    @route.get("{station_uuid}/download", response={200: None, 404: Message})
    def download_meteo_norm(self, station_uuid: str, norm_type: Query[HydrologicalNormTypeFiltersSchema]):
        station = MeteorologicalStation.objects.get(uuid=station_uuid)
        norm_data = MeteorologicalNorm.objects.for_station(station_uuid).filter(norm_type=norm_type.norm_type.value)
        precipitation_df = create_norm_dataframe(
            norm_data.filter(norm_metric=MeteorologicalNormMetric.PRECIPITATION), norm_type.norm_type
        )
        temperature_df = create_norm_dataframe(
            norm_data.filter(norm_metric=MeteorologicalNormMetric.TEMPERATURE), norm_type.norm_type
        )
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            precipitation_df.to_excel(writer, index=False, sheet_name="precipitation")
            temperature_df.to_excel(writer, index=False, sheet_name="temperature")

        output_filename = f"historic-data-meteo-{station.station_code}.xlsx"
        buffer.seek(0)
        response = FileResponse(buffer, as_attachment=True, filename=output_filename)

        return response


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
            include_history=True,
        ).execute_query()

        operational_journal_data.extend(
            daily_hydro_metric_data.values(
                "timestamp_local", "avg_value", "metric_name", "value_code", "sensor_identifier", "has_history"
            )
        )

        cls_estimations_views = [
            EstimationsWaterDischargeDaily,
            EstimationsWaterLevelDailyAverage,
            EstimationsWaterDischargeDailyAverage,
        ]

        for cls in cls_estimations_views:
            estimation_data = cls.objects.filter(**estimations_filter_dict).order_by("timestamp_local")
            operational_journal_data.extend(
                {
                    "timestamp_local": d.timestamp_local.replace(tzinfo=ZoneInfo("UTC")),
                    "avg_value": d.avg_value,
                    "metric_name": d.metric_name,
                }
                for d in estimation_data
            )

        prepared_data = OperationalJournalDataTransformer(operational_journal_data, month, station).get_daily_data()
        return prepared_data

    @route.get("daily-data-virtual", response={200: list[OperationalJournalDailyVirtualDataSchema]})
    def get_daily_data_virtual(self, station_uuid: str, year: int, month: int):
        virtual_station = VirtualStation.objects.get(uuid=station_uuid)
        first_day_current_month = dt(year, month, 1)
        first_day_next_month = first_day_current_month + relativedelta(months=1)
        dt_start = SmartDatetime(first_day_current_month, virtual_station).day_beginning_local.isoformat()
        dt_end = SmartDatetime(first_day_next_month, virtual_station).day_beginning_local.isoformat()

        operational_journal_data = []

        daily_discharge_data = EstimationsWaterDischargeDailyVirtual.objects.filter(
            timestamp_local__range=(dt_start, dt_end), station=virtual_station
        ).order_by("timestamp_local")

        operational_journal_data.extend(daily_discharge_data.values("timestamp_local", "avg_value", "metric_name"))

        daily_average_discharge_data = EstimationsWaterDischargeDailyAverageVirtual.objects.filter(
            timestamp_local__range=(dt_start, dt_end), station=virtual_station
        ).order_by("timestamp_local")

        operational_journal_data.extend(
            daily_average_discharge_data.values("timestamp_local", "avg_value", "metric_name")
        )
        prepared_data = OperationalJournalVirtualDataTransformer(operational_journal_data, month).get_daily_data()

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
            include_history=True,
        ).execute_query()

        prepared_data = OperationalJournalDataTransformer(
            discharge_data.values("timestamp_local", "avg_value", "metric_name", "sensor_identifier", "has_history"),
            month,
            station,
        ).get_discharge_data()

        return prepared_data

    @route.get(
        "decadal-data-virtual",
        response=list[OperationalJournalDecadalHydroVirtualDataSchema],
    )
    def get_virtual_decadal_data(self, station_uuid: str, year: int, month: int):
        station = VirtualStation.objects.get(uuid=station_uuid)
        first_day_current_month = dt(year, month, 1)
        first_day_next_month = first_day_current_month + relativedelta(months=1)

        view_data = EstimationsWaterDischargeDecadeAverageVirtual.objects.filter(
            timestamp_local__range=(first_day_current_month, first_day_next_month),
            station=station,
        ).order_by("timestamp_local")
        decadal_data = [
            {
                "timestamp_local": d.timestamp_local.replace(tzinfo=ZoneInfo("UTC")),
                "avg_value": d.avg_value,
                "metric_name": d.metric_name,
            }
            for d in view_data
        ]
        prepared_data = OperationalJournalVirtualDataTransformer(decadal_data, month).get_hydro_decadal_data()

        return prepared_data

    @route.get(
        "decadal-data-hydro",
        response=list[OperationalJournalDecadalHydroDataSchema],
    )
    def get_hydro_decadal_data(self, station_uuid: str, year: int, month: int):
        station = HydrologicalStation.objects.get(uuid=station_uuid)
        first_day_current_month = dt(year, month, 1)
        first_day_next_month = first_day_current_month + relativedelta(months=1)

        decadal_data = []

        cls_estimations_views = [EstimationsWaterLevelDecadeAverage, EstimationsWaterDischargeDecadeAverage]

        for cls in cls_estimations_views:
            view_data = cls.objects.filter(
                timestamp_local__range=(first_day_current_month, first_day_next_month),
                station=station,
            ).order_by("timestamp_local")

            decadal_data.extend(
                {
                    "timestamp_local": d.timestamp_local.replace(tzinfo=ZoneInfo("UTC")),
                    "avg_value": d.avg_value,
                    "metric_name": d.metric_name,
                    "sensor_identifier": d.sensor_identifier,
                }
                for d in view_data
            )

        prepared_data = OperationalJournalDataTransformer(decadal_data, month, station).get_hydro_decadal_data()
        return prepared_data

    @route.get(
        "decadal-data-meteo",
        response=list[OperationalJournalDecadalMeteoDataSchema],
    )
    def get_meteo_decadal_data(self, station_uuid: str, year: int, month: int):
        station = MeteorologicalStation.objects.get(uuid=station_uuid)
        first_day_current_month = dt(year, month, 1)
        dt_start = SmartDatetime(first_day_current_month, station).day_beginning_local.isoformat()
        first_day_next_month = first_day_current_month + relativedelta(months=1)
        dt_end = SmartDatetime(first_day_next_month, station).day_beginning_local.isoformat()

        meteo_data = TimeseriesQueryManager(
            model=MeteorologicalMetric,
            order_param="timestamp_local",
            order_direction="ASC",
            filter_dict={
                "timestamp_local__gte": dt_start,
                "timestamp_local__lt": dt_end,
                "station": station.id,
                "metric_name__in": [
                    MeteorologicalMetricName.AIR_TEMPERATURE_DECADE_AVERAGE,
                    MeteorologicalMetricName.PRECIPITATION_DECADE_AVERAGE,
                ],
            },
        ).execute_query()

        prepared_data = OperationalJournalDataTransformer(
            meteo_data.values("timestamp_local", "value", "metric_name"), month, station
        ).get_meteo_decadal_data()

        return prepared_data


@api_controller(
    "bulk-data/{organization_uuid}", tags=["Bulk data download"], auth=JWTAuth(), permissions=regular_permissions
)
class BulkDataAPIController:
    @route.post("download")
    def download_bulk_data(self, request, organization_uuid: str, payload: BulkDataDownloadInputSchema):
        all = False
        if (
            len(
                payload.hydro_station_manual_uuids
                + payload.hydro_station_auto_uuids
                + payload.meteo_station_uuids
                + payload.virtual_station_uuids
            )
            == 0
        ):
            all = True
        else:
            hydro_station_uuids = payload.hydro_station_manual_uuids + payload.hydro_station_auto_uuids
            if (
                not hydro_station_uuids_belong_to_organization_uuid(hydro_station_uuids, organization_uuid)
                and meteo_station_uuids_belong_to_organization_uuid(payload.meteo_station_uuids, organization_uuid)
                and virtual_station_uuids_belong_to_organization_uuid(payload.virtual_station_uuids, organization_uuid)
            ):
                raise PermissionDenied("The provided station UUIDs do not belong to the organization.")

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            write_bulk_data_hydro_manual_sheets(
                writer=writer, station_uuids=payload.hydro_station_manual_uuids, org_uuid=organization_uuid, all=all
            )
            write_bulk_data_meteo_sheets(
                writer=writer, station_uuids=payload.meteo_station_uuids, org_uuid=organization_uuid, all=all
            )
            write_bulk_data_virtual_sheets(
                writer=writer, station_uuids=payload.virtual_station_uuids, org_uuid=organization_uuid, all=all
            )
            write_bulk_data_hydro_auto_sheets(
                writer=writer, station_uuids=payload.hydro_station_auto_uuids, org_uuid=organization_uuid, all=all
            )

        output_filename = "bulk-data.xlsx"
        buffer.seek(0)
        response = FileResponse(buffer, as_attachment=True, filename=output_filename)

        return response
