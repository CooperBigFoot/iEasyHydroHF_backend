from typing import Any

from django.db import connection
from zoneinfo import ZoneInfo

from sapphire_backend.metrics.timeseries.query import TimeseriesQueryManager

from .schema import EstimationsViewSchema


class EstimationsViewQueryManager(TimeseriesQueryManager):
    def __init__(
        self,
        model: EstimationsViewSchema,
        filter_dict: dict[str, str | list[str]] = None,
        order_param: str = "timestamp_local",
        order_direction: str = "DESC",
    ):
        super().__init__(model, filter_dict, order_param, order_direction)

    @staticmethod
    def _set_model(
        model: EstimationsViewSchema,
    ):
        if model not in [
            "estimations_water_level_daily_average",
            "estimations_water_level_decade_average",
            "estimations_water_discharge_daily",
            "estimations_water_discharge_daily_average",
            "estimations_water_discharge_fiveday_average",
            "estimations_water_discharge_decade_average",
        ]:
            raise ValueError("EstimationsViewQueryManager can only be instantiated with an existing view.")
        return model

    def _add_filter_fields(self):
        return ["avg_value", "timestamp_local", "station_id"]

    def _validate_filter_dict(self):
        if "station_id" not in self.filter_dict:
            raise ValueError("EstimationsViewQueryManager requires filtering by station ID")

        for key in self.filter_dict.keys():
            cleaned_key = key.split("__")[0]
            if cleaned_key not in self.filter_fields:
                raise ValueError(f"{cleaned_key} field does not exist on the {self.model} view.")

    def _construct_filter(self) -> dict[str, Any]:
        self._validate_filter_dict()
        return self.filter_dict

    def _construct_sql_filter_string(self):
        where_clauses = []
        params = []

        if self.filter_dict is not None:
            for field, value in self.filter_dict.items():
                match field:
                    case "timestamp_local":
                        where_clauses.append("timestamp_local = %s")
                        params.append(value)
                    case "timestamp_local__gt":
                        where_clauses.append("timestamp_local > %s")
                        params.append(value)
                    case "timestamp_local__gte":
                        where_clauses.append("timestamp_local >= %s")
                        params.append(value)
                    case "timestamp_local__lt":
                        where_clauses.append("timestamp_local < %s")
                        params.append(value)
                    case "timestamp_local__lte":
                        where_clauses.append("timestamp_local <= %s")
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
                        where_clauses.append("station_id = %s")
                        params.append(value)
                    case "station_id__in":
                        placeholders = ", ".join(["%s"] * len(value))
                        where_clauses.append(f"station_id IN ({placeholders})")
                        params.extend(value)
                    case _:
                        raise ValueError(f"{field} field does not exist on the {self.model} view.")

        where_clause = " AND ".join(where_clauses)
        return where_clause, params

    def execute_query(self, limit: int = 100):
        where_string, params = self._construct_sql_filter_string()

        query = f"""
            SELECT
            timestamp_local, avg_value
            FROM {self.model}
            WHERE {where_string}
            ORDER BY timestamp_local {self.order_direction}
            LIMIT %s
        """

        with connection.cursor() as cursor:
            cursor.execute(query, [*params, limit])
            rows = cursor.fetchall()

        results = [{"timestamp_local": row[0].astimezone(ZoneInfo("UTC")), "avg_value": row[1]} for row in rows]
        return results
