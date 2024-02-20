from typing import Any

from django.db import connection
from django.db.models import Count

from sapphire_backend.organizations.models import Organization
from sapphire_backend.stations.models import HydrologicalStation, MeteorologicalStation, Site

from ..models import HydrologicalMetric, MeteorologicalMetric


class TimeseriesQueryManager:
    def __init__(
        self,
        model: type[HydrologicalMetric] | type[MeteorologicalMetric],
        organization_uuid: str,
        filter_dict: dict[str, str | list[str]] = None,
        order_param: str = "timestamp",
        order_direction: str = "DESC",
    ):
        self.model = self._set_model(model)
        self.organization = self._set_organization(organization_uuid)
        self.filter_dict = filter_dict
        self.order_param = order_param
        self.order_direction = order_direction
        self.order = self._construct_order()
        self.filter = self._construct_filter(organization_uuid)

    @staticmethod
    def _set_model(model: HydrologicalMetric | MeteorologicalMetric):
        if model not in [HydrologicalMetric, MeteorologicalMetric]:
            raise ValueError(
                "TimeseriesQueryManager can only be instantiated with HydrologicalMetric or MeteorologicalMetric."
            )

        return model

    @staticmethod
    def _set_organization(organization_uuid: str):
        try:
            return Organization.objects.get(uuid=organization_uuid)
        except Organization.DoesNotExist:
            raise ValueError("Organization with the given UUID does not exist.")

    def _validate_filter_dict(self):
        field_names = [field.name for field in self.model._meta.get_fields()]
        for key in self.filter_dict.keys():
            cleaned_key = key.split("__")[0]
            if cleaned_key not in field_names:
                raise ValueError(f"{cleaned_key} field does not exist on the {self.model._meta.object_name} model.")

    @staticmethod
    def _resolve_order_direction(order_direction: str) -> str:
        return "-" if order_direction == "DESC" else ""

    def _construct_order(self) -> str:
        return f"{self._resolve_order_direction(self.order_direction)}{self.order_param}"

    def _construct_filter(self, organization_uuid: str) -> dict[str, Any]:
        if self.filter_dict:
            self._validate_filter_dict()
        filter_dict = {"station__site__organization": organization_uuid}

        if self.filter_dict:
            filter_dict.update(self.filter_dict)

        return filter_dict

    def _construct_organization_sql_join_string(self):
        db_table = self.model._meta.db_table
        station_table = (
            HydrologicalStation._meta.db_table
            if self.model == HydrologicalMetric
            else MeteorologicalStation._meta.db_table
        )
        site_table = Site._meta.db_table
        organization_table = Organization._meta.db_table

        return f"""
            JOIN {station_table} st ON st.id = {db_table}.station_id
            JOIN {site_table} s ON s.uuid = st.site_id
            JOIN {organization_table} o ON o.uuid = s.organization_id
        """

    def _construct_sql_filter_string(self):
        where_clauses = [f"o.uuid='{self.organization.uuid}'"]
        params = []

        if self.filter_dict is not None:
            for field, value in self.filter_dict.items():
                match field:
                    case "timestamp":
                        where_clauses.append("timestamp = %s")
                        params.append(value)
                    case "timestamp__gt":
                        where_clauses.append("timestamp > %s")
                        params.append(value)
                    case "timestamp__gte":
                        where_clauses.append("timestamp >= %s")
                        params.append(value)
                    case "timestamp__lt":
                        where_clauses.append("timestamp < %s")
                        params.append(value)
                    case "timestamp__lte":
                        where_clauses.append("timestamp <= %s")
                        params.append(value)
                    case "avg_value__gt":
                        where_clauses.append("avg_value > %s")
                        params.append(value)
                    case "avg_value__gte":
                        where_clauses.append("avg_value >= %s")
                        params.append(value)
                    case "avg_value__lt":
                        where_clauses.append("avg_value < %s")
                        params.append(value)
                    case "avg_value__lte":
                        where_clauses.append("avg_value <= %s")
                        params.append(value)
                    case "station_id":
                        where_clauses.append("st.id = %s")
                        params.append(value)
                    case "station__station_code":
                        where_clauses.append("st.station_code = %s")
                        params.append(value)
                    case "station_id__in":
                        placeholders = ", ".join(["%s"] * len(value))
                        where_clauses.append(f"st.id IN ({placeholders})")
                        params.extend(value)
                    case "station__station_code__in":
                        placeholders = ", ".join(["%s"] * len(value))
                        where_clauses.append(f"st.station_code IN ({placeholders})")
                        params.extend(value)
                    case "metric_name":
                        where_clauses.append("metric_name = %s")
                        params.append(value)
                    case "value_type":
                        where_clauses.append("value_type = %s")
                        params.append(value)
                    case "sensor_identifier":
                        where_clauses.append("sensor_identifier = %s")
                        params.append(value)
                    case _:
                        raise ValueError(f"{field} field does not exist on the {self.model._meta.object_name} model.")

        where_clause = " AND ".join(where_clauses)
        return where_clause, params

    def execute_query(self):
        return self.model.objects.filter(**self.filter).order_by(self.order)

    def get_total(self):
        return self.model.objects.filter(**self.filter).count()

    def get_metric_distribution(self):
        return (
            self.model.objects.filter(**self.filter).values("metric_name").annotate(metric_count=Count("metric_name"))
        )

    def get_value_type_distribution(self):
        return (
            self.model.objects.filter(**self.filter)
            .values("value_type")
            .annotate(value_type_count=Count("value_type"))
        )

    def time_bucket(self, interval: str, agg_func: str, limit: int = 100):
        db_table = self.model._meta.db_table
        join_string = self._construct_organization_sql_join_string()
        where_string, params = self._construct_sql_filter_string()

        query = f"""
            SELECT
            time_bucket(%s, timestamp) AS bucket,
            {agg_func}(avg_value)
            FROM {db_table}
            {join_string}
            WHERE {where_string}
            GROUP BY bucket
            ORDER BY bucket {self.order_direction}
            LIMIT %s
        """

        with connection.cursor() as cursor:
            cursor.execute(query, [interval, *params, limit])
            rows = cursor.fetchall()

        results = [{"bucket": row[0], "value": row[1]} for row in rows]
        return results
