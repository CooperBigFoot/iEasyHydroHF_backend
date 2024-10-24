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
from django.db.models import Avg, Case, Count, DecimalField, Max, Min, Sum, Value, When
from django.http import FileResponse
from django.templatetags.static import static
from ninja import File, Query
from ninja.files import UploadedFile
from ninja_extra import api_controller, route
from ninja_extra.pagination import PageNumberPaginationExtra, PaginatedResponseSchema, paginate
from ninja_jwt.authentication import JWTAuth
from zoneinfo import ZoneInfo

from sapphire_backend.stations.models import HydrologicalStation, MeteorologicalStation
from sapphire_backend.utils.datetime_helper import SmartDatetime
from sapphire_backend.utils.mixins.schemas import Message
from sapphire_backend.utils.permissions import (
    regular_permissions,
)
from sapphire_backend.utils.rounding import custom_ceil, hydrological_round

from ..estimations.models import (
    EstimationsWaterDischargeDaily,
    EstimationsWaterDischargeDailyAverage,
    EstimationsWaterDischargeDecadeAverage,
    EstimationsWaterLevelDailyAverage,
    EstimationsWaterLevelDecadeAverage,
    HydrologicalRound,
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
    MetricTotalCountSchema,
    OperationalJournalDailyDataSchema,
    OperationalJournalDecadalDataStationType,
    OperationalJournalDecadalHydroDataSchema,
    OperationalJournalDecadalMeteoDataSchema,
    OperationalJournalDischargeDataSchema,
    OrderQueryParamSchema,
    TimeBucketQueryParams,
    TimestampGroupedHydroMetricSchema,
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
    create_norm_dataframe,
    hydro_station_uuids_belong_to_organization_uuid,
    meteo_station_uuids_belong_to_organization_uuid,
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
    def _validate_datetime_range(filter_dict):
        start = filter_dict.get("timestamp_local__gte") or filter_dict.get("timestamp_local__gt")
        end = filter_dict.get("timestamp_local__lt") or filter_dict.get("timestamp_local__lte")

        date_range = end - start

        if date_range.days > 30:
            raise ValueError("Date range cannot be more than 30 days")

    @route.get("grouped", response={200: PaginatedResponseSchema[TimestampGroupedHydroMetricSchema]})
    @paginate(PageNumberPaginationExtra, page_size=100, max_page_size=101)
    def get_grouped_hydro_metrics(
        self,
        organization_uuid: str,
        order: Query[OrderQueryParamSchema],
        filters: Query[HydroMetricFilterSchema] = None,
    ):
        filter_dict = filters.dict(exclude_none=True)
        filter_dict["station__site__organization"] = organization_uuid

        self._validate_datetime_range(filter_dict)

        order_param, order_direction = order.order_param, order.order_direction
        qm = TimeseriesQueryManager(
            model=HydrologicalMetric,
            order_param=order_param,
            order_direction=order_direction,
            filter_dict=filter_dict,
        )
        qs = qm.execute_query()

        annotations = {}
        for metric in filter_dict.get("metric_name__in"):
            annotations[metric] = Max(
                Case(
                    When(metric_name=metric, then=HydrologicalRound("avg_value")),
                    default=Value(None),
                    output_field=DecimalField(),
                )
            )
        qs = qs.values("timestamp_local").annotate(**annotations).order_by(qm.order)

        return qs

    @route.get("", response={200: PaginatedResponseSchema[HydrologicalMetricOutputSchema]})
    @paginate(PageNumberPaginationExtra, page_size=100, max_page_size=101)
    def get_hydro_metrics(
        self,
        organization_uuid: str,
        order: Query[OrderQueryParamSchema],
        filters: Query[HydroMetricFilterSchema] = None,
    ):
        filter_dict = filters.dict(exclude_none=True)
        filter_dict["station__site__organization"] = organization_uuid

        self._validate_datetime_range(filter_dict)

        order_param, order_direction = order.order_param, order.order_direction
        qm = TimeseriesQueryManager(
            model=HydrologicalMetric,
            order_param=order_param,
            order_direction=order_direction,
            filter_dict=filter_dict,
        )
        qs = qm.execute_query()

        return qs

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
        ).execute_query()

        operational_journal_data.extend(
            daily_hydro_metric_data.values("timestamp_local", "avg_value", "metric_name", "value_code")
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

    @route.get(
        "decadal-data/{station_type}",
        response=list[OperationalJournalDecadalHydroDataSchema | OperationalJournalDecadalMeteoDataSchema],
    )
    def get_decadal_data(
        self, station_uuid: str, year: int, month: int, station_type: OperationalJournalDecadalDataStationType
    ):
        if station_type.station_type == "hydro":
            station = HydrologicalStation.objects.get(uuid=station_uuid)
        else:
            station = MeteorologicalStation.objects.get(uuid=station_uuid)
        first_day_current_month = dt(year, month, 1)
        dt_start = SmartDatetime(first_day_current_month, station).day_beginning_local.isoformat()
        first_day_next_month = first_day_current_month + relativedelta(months=1)
        dt_end = SmartDatetime(first_day_next_month, station).day_beginning_local.isoformat()

        decadal_data = []

        if station_type.station_type == "hydro":
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
                    }
                    for d in view_data
                )
        else:
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

            decadal_data.extend(meteo_data.values("timestamp_local", "value", "metric_name"))

        if station_type.station_type == "hydro":
            prepared_data = OperationalJournalDataTransformer(decadal_data).get_hydro_decadal_data()
        else:
            prepared_data = OperationalJournalDataTransformer(decadal_data).get_meteo_decadal_data()

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
