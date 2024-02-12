from typing import Any

from django.db.models import Count

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
        self.filter_value = filter_value
        self.filter_dict = filter_dict
        self.order_param = order_param
        self.order_direction = self._resolve_order_direction(order_direction)
        self.order = self._construct_order()
        self.filter = self._construct_filter(organization_uuid)

    @staticmethod
    def _resolve_order_direction(order_direction: str) -> str:
        return "-" if order_direction == "DESC" else ""

    def _construct_order(self) -> str:
        return f"{self.order_direction}{self.order_param}"

    def _construct_filter(self, organization_uuid: str) -> dict[str, Any]:
        filter_dict = {"station__site__organization": organization_uuid}
        if self.filter_dict:
            filter_dict.update(self.filter_dict)

        elif self.filter_param:
            filter_dict.update({f"{self.filter_param}__{self.filter_operator}": {self.filter_value}})

        return filter_dict

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
