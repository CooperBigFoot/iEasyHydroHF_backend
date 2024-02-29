import logging

from django import db
from django.db import IntegrityError, connection, models, InternalError
from django.utils.translation import gettext_lazy as _

from .choices import (
    HydrologicalMeasurementType,
    HydrologicalMetricName,
    MeteorologicalMeasurementType,
    MeteorologicalMetricName,
    MetricUnit,
)
from .managers import HydrologicalMetricQuerySet, MeteorologicalMetricQuerySet


class HydrologicalMetric(models.Model):
    timestamp = models.DateTimeField(primary_key=True, verbose_name=_("Timestamp"))
    min_value = models.DecimalField(
        verbose_name=_("Minimum value"), max_digits=15, decimal_places=5, null=True, blank=True
    )
    avg_value = models.DecimalField(verbose_name=_("Average value"), max_digits=15, decimal_places=5)
    max_value = models.DecimalField(
        verbose_name=_("Maximum value"), max_digits=15, decimal_places=5, null=True, blank=True
    )
    unit = models.CharField(verbose_name=_("Unit"), choices=MetricUnit, blank=True, max_length=20)
    value_type = models.CharField(
        verbose_name=_("Value type"),
        choices=HydrologicalMeasurementType,
        default=HydrologicalMeasurementType.UNKNOWN,
        max_length=2,
        blank=False,
    )
    metric_name = models.CharField(
        verbose_name=_("Metric name"),
        choices=HydrologicalMetricName,
        max_length=20,
        blank=False,
    )
    station = models.ForeignKey("stations.HydrologicalStation", verbose_name=_("Station"), on_delete=models.PROTECT)

    sensor_identifier = models.CharField(verbose_name=_("Sensor identifier"), blank=True, max_length=50)
    sensor_type = models.CharField(verbose_name=_("Sensor type"), blank=True, max_length=50)

    objects = HydrologicalMetricQuerySet.as_manager()

    class Meta:
        verbose_name = _("Hydrological metric")
        verbose_name_plural = _("Hydrological metrics")
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.metric_name}, {self.station.name} on {self.timestamp}"

    def delete(self, **kwargs):
        sql_query_delete = f"""
        DELETE FROM metrics_hydrologicalmetric WHERE
        timestamp = '{self.timestamp}' AND
        station_id = {self.station_id} AND
        metric_name = '{self.metric_name}' AND
        value_type = '{self.value_type}' AND
        sensor_identifier = '{self.sensor_identifier}';"""

        with connection.cursor() as cursor:
            try:
                cursor.execute(sql_query_delete)
            except db.utils.InternalError as e:
                # If btree exception occurs, the record was probably already deleted so it doesn't affect
                # functionality
                raise Exception(f"Delete statement {sql_query_delete} failed. {e}")

    def save(self, upsert=True, **kwargs) -> None:
        min_value = self.min_value
        max_value = self.max_value
        avg_value = self.avg_value

        if self.min_value is None:
            min_value = "NULL"
        if self.max_value is None:
            max_value = "NULL"
        if self.avg_value is None:
            avg_value = "NULL"

        sql_query_insert = """
            INSERT INTO metrics_hydrologicalmetric
            (timestamp, station_id, metric_name, value_type, sensor_identifier, min_value, avg_value, max_value,
            unit, sensor_type)
            VALUES ('{timestamp}', {station_id}, '{metric_name}', '{value_type}', '{sensor_identifier}', {min_value},
            {avg_value}, {max_value}, '{unit}', '{sensor_type}');
            """.format(
            timestamp=self.timestamp,
            station_id=self.station_id,
            metric_name=self.metric_name,
            value_type=self.value_type,
            sensor_identifier=self.sensor_identifier,
            min_value=min_value,
            avg_value=avg_value,
            max_value=max_value,
            unit=self.unit,
            sensor_type=self.sensor_type,
        )

        sql_query_upsert = """
            INSERT INTO metrics_hydrologicalmetric (timestamp, station_id, metric_name, value_type, sensor_identifier, min_value, avg_value, max_value, unit, sensor_type)
            VALUES ('{timestamp}', {station_id}, '{metric_name}', '{value_type}', '{sensor_identifier}', {min_value},
            {avg_value}, {max_value}, '{unit}', '{sensor_type}')
            ON CONFLICT (timestamp, station_id, metric_name, value_type, sensor_identifier)
            DO UPDATE
            SET min_value = EXCLUDED.min_value,
                avg_value = EXCLUDED.avg_value,
                max_value = EXCLUDED.max_value,
                unit = EXCLUDED.unit,
                sensor_type = EXCLUDED.sensor_type;
        """.format(
            timestamp=self.timestamp,
            station_id=self.station_id,
            metric_name=self.metric_name,
            value_type=self.value_type,
            sensor_identifier=self.sensor_identifier,
            min_value=min_value,
            avg_value=avg_value,
            max_value=max_value,
            unit=self.unit,
            sensor_type=self.sensor_type,
        )
        try:
            with connection.cursor() as cursor:
                if upsert:
                    cursor.execute(sql_query_upsert)
                else:
                    cursor.execute(sql_query_insert)
        except db.utils.NotSupportedError as e:
            """
            Handle specific error. Timescale has this bug, hyper chunks should not have insert blockers.
            E.g.:
            invalid INSERT on the root table of hypertable "_hyper_1_104_chunk"
            HINT:  Make sure the TimescaleDB extension has been preloaded.
            """
            if 'invalid INSERT on the root table of hypertable "' in str(e):
                hyper_chunk_name = (
                    str(e).split('invalid INSERT on the root table of hypertable "')[1].split('"')[0]
                )
                if hyper_chunk_name.startswith("_hyper") and hyper_chunk_name.endswith("_chunk"):
                    sql_query_remove_trigger = (
                        f"drop trigger ts_insert_blocker on _timescaledb_internal.{hyper_chunk_name}; "
                    )
                    cursor.execute(sql_query_remove_trigger)
                    logging.info(f"Removed unwanted ts_insert_blocker on {hyper_chunk_name}")
                    cursor.execute(sql_query_insert)
                else:
                    raise Exception(e)
            else:
                raise Exception(e)
        except Exception as e:
            raise Exception(e)


class MeteorologicalMetric(models.Model):
    timestamp = models.DateTimeField(primary_key=True, verbose_name=_("Timestamp"))
    value = models.DecimalField(verbose_name=_("Value"), max_digits=10, decimal_places=5)
    value_type = models.CharField(
        verbose_name=_("Value type"),
        choices=MeteorologicalMeasurementType,
        default=MeteorologicalMeasurementType.UNKNOWN,
        max_length=2,
        blank=False,
    )
    metric_name = models.CharField(
        verbose_name=_("Metric name"),
        choices=MeteorologicalMetricName,
        max_length=20,
        blank=False,
    )
    unit = models.CharField(verbose_name=_("Unit"), choices=MetricUnit, max_length=20, blank=True)
    station = models.ForeignKey("stations.MeteorologicalStation", verbose_name=_("Station"), on_delete=models.PROTECT)

    objects = MeteorologicalMetricQuerySet.as_manager()

    class Meta:
        verbose_name = _("Meteorological metric")
        verbose_name_plural = _("Meteorological metrics")
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.metric_name}, {self.station.name} on {self.timestamp}"

    def delete(self, **kwargs) -> None:
        sql_query_delete = f"""
        DELETE FROM metrics_meteorologicalmetric WHERE
        timestamp = '{self.timestamp}' AND
        station_id = {self.station_id} AND
        metric_name = '{self.metric_name}';"""
        with connection.cursor() as cursor:
            cursor.execute(sql_query_delete)

    def save(self, upsert=True, **kwargs) -> None:
        sql_query_insert = """
        INSERT INTO metrics_meteorologicalmetric (timestamp, station_id, metric_name, value, value_type, unit )
        VALUES ('{timestamp}'::timestamp, {station_id}, '{metric_name}', {value}, '{value_type}', '{unit}');
        """.format(
            timestamp=self.timestamp,
            station_id=self.station_id,
            metric_name=self.metric_name,
            value=self.value,
            value_type=self.value_type,
            unit=self.unit,
        )

        with connection.cursor() as cursor:
            try:
                cursor.execute(sql_query_insert)
            except IntegrityError:
                if upsert:
                    self.delete()
                cursor.execute(sql_query_insert)
