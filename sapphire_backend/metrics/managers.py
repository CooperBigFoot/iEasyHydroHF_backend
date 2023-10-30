from django.db.models import F, Func, Manager, QuerySet


class TimeSeriesQuerySet(QuerySet):
    def time_bucket(self, interval: str, field_name: str = "timestamp"):
        return self.annotate(bucket=Func(F(field_name), interval, function="time_bucket"))


class TimeSeriesManager(Manager.from_queryset(TimeSeriesQuerySet)):
    pass
