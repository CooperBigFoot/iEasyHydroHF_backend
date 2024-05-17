from typing import Any

from django.db import connection
from django.db.models import Count
from django.db.utils import DataError, ProgrammingError

from sapphire_backend.organizations.models import Organization
from sapphire_backend.stations.models import HydrologicalStation, MeteorologicalStation, Site

from ..models import HydrologicalMetric, MeteorologicalMetric


class TimeseriesQueryManager:
    def __init__(
        self,
        model: type[HydrologicalMetric] | type[MeteorologicalMetric],
        filter_dict: dict[str, str | list[str]] = None,
        order_param: str = "timestamp",
        order_direction: str = "DESC",
    ):
        self.model = self._set_model(model)
        self.filter_fields = self._add_filter_fields()
        self.filter_dict = filter_dict if filter_dict else {}
        self._validate_filter_dict()
        self.order_param = order_param
        self.order_direction = order_direction
        self.order = self._construct_order()

    @staticmethod
    def _set_model(model: HydrologicalMetric | MeteorologicalMetric):
        if model not in [HydrologicalMetric, MeteorologicalMetric]:
            raise ValueError(
                "TimeseriesQueryManager can only be instantiated with HydrologicalMetric or MeteorologicalMetric."
            )

        return model

    def _add_filter_fields(self):
        return [field.name for field in self.model._meta.get_fields()]

    def _validate_filter_dict(self):
        for key in self.filter_dict.keys():
            cleaned_key = key.split("__")[0]
            if cleaned_key not in self.filter_fields:
                raise ValueError(f"{cleaned_key} field does not exist on the {self.model._meta.object_name} model.")

    @staticmethod
    def _resolve_order_direction(order_direction: str) -> str:
        return "-" if order_direction == "DESC" else ""

    def _construct_order(self) -> str:
        return f"{self._resolve_order_direction(self.order_direction)}{self.order_param}"

    def _construct_filter(self) -> dict[str, Any]:
        if self.filter_dict:
            self._validate_filter_dict()

        return self.filter_dict

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
        where_clauses = []
        params = []

        if self.filter_dict:
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
                    case "station__site__organization":
                        where_clauses.append("o.uuid = %s")
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
                    case "station":
                        where_clauses.append("station_id = %s")
                        params.append(value)
                    case "station__station_code":
                        where_clauses.append("st.station_code = %s")
                        params.append(value)
                    case "station__in":
                        placeholders = ", ".join(["%s"] * len(value))
                        where_clauses.append(f"station_id IN ({placeholders})")
                        params.extend(value)
                    case "station__station_code__in":
                        placeholders = ", ".join(["%s"] * len(value))
                        where_clauses.append(f"st.station_code IN ({placeholders})")
                        params.extend(value)
                    case "metric_name__in":
                        placeholders = ", ".join(["%s"] * len(value))
                        where_clauses.append(f"metric_name IN ({placeholders})")
                        params.extend(value)
                    case "value_type__in":
                        placeholders = ", ".join(["%s"] * len(value))
                        where_clauses.append(f"value_type IN ({placeholders})")
                        params.extend(value)
                    case "sensor_identifier":
                        where_clauses.append("sensor_identifier = %s")
                        params.append(value)
                    case _:
                        raise ValueError(f"{field} field does not exist on the {self.model._meta.object_name} model.")

        where_clause = " AND ".join(where_clauses)
        return where_clause, params

    def execute_query(self):
        return self.model.objects.filter(**self.filter_dict).order_by(self.order)

    def get_total(self):
        return self.model.objects.filter(**self.filter_dict).count()

    def get_metric_distribution(self):
        return (
            self.model.objects.filter(**self.filter_dict)
            .values("metric_name")
            .annotate(metric_count=Count("metric_name"))
        )

    def get_value_type_distribution(self):
        return (
            self.model.objects.filter(**self.filter_dict)
            .values("value_type")
            .annotate(value_type_count=Count("value_type"))
        )

    def time_bucket(self, interval: str, agg_func: str, limit: int = 100):
        db_table = self.model._meta.db_table
        join_string = (
            self._construct_organization_sql_join_string()
            if "station__site__organization" or "station__station_code" in self.filter_dict
            else ""
        )
        where_string, params = self._construct_sql_filter_string()
        where_clause = f"WHERE {where_string}" if where_string else ""

        query = f"""
            SELECT
            time_bucket(%s, timestamp) AS bucket,
            {agg_func}(avg_value)
            FROM {db_table}
            {join_string}
            {where_clause}
            GROUP BY bucket
            ORDER BY bucket {self.order_direction}
            LIMIT %s
        """

        try:
            with connection.cursor() as cursor:
                cursor.execute(query, [interval, *params, limit])
                rows = cursor.fetchall()
        except DataError:
            raise ValueError("Invalid time bucket interval")
        except ProgrammingError:
            raise ValueError("Invalid aggregation function")
        finally:
            connection.close()

        results = [{"bucket": row[0], "value": row[1]} for row in rows]
        return results
