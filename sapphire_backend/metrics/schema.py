from datetime import datetime

from ninja import Schema


class TimeseriesFiltersSchema(Schema):
    timestamp__lte: datetime
    timestamp__gte: datetime
    average_value__lte: float
    average_value__gte: float


class TimeseriesOrderSchema(Schema):
    timestamp: str


class LatestMetricOutputSchema(Schema):
    timestamp: datetime


class TimeseriesOutputSchema(Schema):
    timestamp: datetime
