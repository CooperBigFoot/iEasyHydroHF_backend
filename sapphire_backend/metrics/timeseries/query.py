from typing import Any

from django.db import connection
from django.db.models import Count

from sapphire_backend.organizations.models import Organization
from sapphire_backend.stations.models import HydrologicalStation, MeteorologicalStation, Site

from ..models import HydrologicalMetric, MeteorologicalMetric


class TimeseriesQueryManager:
    def __init__(
        self,
        model: HydrologicalMetric | MeteorologicalMetric,
        organization_uuid: str,
        filter_param: str = None,
        filter_operator: str = None,
        filter_value: Any = None,
        filter_dict: dict[str, str] = None,
        order_param: str = "timestamp",
        order_direction: str = "DESC",
    ):
        self.model = model
        self.filter_param = filter_param
        self.filter_operator = filter_operator
        self.organization_uuid = organization_uuid
        self.filter_value = filter_value
        self.filter_dict = filter_dict
        self.order_param = order_param
        self.order_direction = order_direction
        self.order = self._construct_order()
        self.filter = self._construct_filter(organization_uuid)

    @staticmethod
    def _resolve_order_direction(order_direction: str) -> str:
        return "-" if order_direction == "DESC" else ""

    def _construct_order(self) -> str:
        return f"{self._resolve_order_direction(self.order_direction)}{self.order_param}"

    def _construct_filter(self, organization_uuid: str) -> dict[str, Any]:
        filter_dict = {"station__site__organization": organization_uuid}
        if self.filter_dict:
            filter_dict.update(self.filter_dict)

        elif self.filter_param:
            filter_dict.update({f"{self.filter_param}__{self.filter_operator}": {self.filter_value}})

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
            JOIN {site_table} s  ON s.uuid = st.site_id
            JOIN {organization_table} o ON o.uuid = s.organization_id
        """

    def _construct_sql_filter_string(self):
        where_clauses = []
        params = []
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
                case "avg_value":
                    where_clauses.append("avg_value = %s")
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
        where_string = self._construct_sql_filter_string()

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
        print(query)

        with connection.cursor() as cursor:
            cursor.execute(query, [interval, limit])
            rows = cursor.fetchall()

        results = [{"bucket": row[0], "timestamp": row[1]} for row in rows]
        return results
