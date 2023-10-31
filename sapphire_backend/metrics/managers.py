from django.db.models import DateTimeField, F, Func, Manager, QuerySet, Value


class TimeSeriesQuerySet(QuerySet):
    def time_bucket(self, interval: str, field_name: str = "timestamp"):
        return self.annotate(
            bucket=Func(Value(interval), F(field_name), function="time_bucket", output_field=DateTimeField())
        )


class TimeSeriesManager(Manager.from_queryset(TimeSeriesQuerySet)):
    pass
