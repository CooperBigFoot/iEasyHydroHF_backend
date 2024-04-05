from typing import Any, Literal

from django.db import connection

from sapphire_backend.metrics.timeseries.query import TimeseriesQueryManager
from sapphire_backend.stations.models import HydrologicalStation


class EstimationsViewQueryManager(TimeseriesQueryManager):
    def __init__(
        self,
        model: Literal[
            "estimations_water_level_daily_average",
            "estimations_water_discharge_daily",
            "estimations_water_discharge_daily_average",
            "estimations_water_discharge_fiveday_average",
            "estimations_water_discharge_decade_average",
        ],
        organization_uuid: str,
        filter_dict: dict[str, str | list[str]] = None,
        order_param: str = "timestamp",
        order_direction: str = "DESC",
    ):
        super().__init__(model, organization_uuid, filter_dict, order_param, order_direction)

    @staticmethod
    def _set_model(
        model: Literal[
            "estimations_water_level_daily_average",
            "estimations_water_discharge_daily",
            "estimations_water_discharge_daily_average",
            "estimations_water_discharge_fiveday_average",
            "estimations_water_discharge_decade_average",
        ],
    ):
        if model not in [
            "estimations_water_level_daily_average",
            "estimations_water_discharge_daily",
            "estimations_water_discharge_daily_average",
            "estimations_water_discharge_fiveday_average",
            "estimations_water_discharge_decade_average",
        ]:
            raise ValueError("EstimationsViewQueryManager can only be instantiated with an existing view.")
        return model

    def _add_filter_fields(self):
        return ["avg_value", "timestamp", "station_id"]

    def _validate_filter_dict(self):
        if "station_id" not in self.filter_dict and "station_id__uuid" not in self.filter_dict:
            raise ValueError("EstimationsViewQueryManager requires filtering by station ID")

        if not HydrologicalStation.objects.filter(
            site_id__in=[*self.organization.site_related.values_list("uuid", flat=True)],
            id=self.filter_dict["station_id"],
        ).exists():
            raise ValueError(f"Station with the ID {self.filter_dict['station_id']} does not exist.")

        for key in self.filter_dict.keys():
            cleaned_key = key.split("__")[0]
            if cleaned_key not in self.filter_fields:
                raise ValueError(f"{cleaned_key} field does not exist on the {self.model} view.")

    def _construct_filter(self, organization_uuid: str) -> dict[str, Any]:
        self._validate_filter_dict()
        return self.filter_dict

    def _construct_sql_filter_string(self):
        where_clauses = []
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
            timestamp, avg_value
            FROM {self.model}
            WHERE {where_string}
            ORDER BY timestamp {self.order_direction}
            LIMIT %s
        """

        try:
            with connection.cursor() as cursor:
                cursor.execute(query, [*params, limit])
                rows = cursor.fetchall()
        finally:
            connection.close()

        results = [{"timestamp": row[0], "value": row[1]} for row in rows]
        return results
