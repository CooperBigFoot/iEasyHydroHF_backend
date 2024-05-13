import logging
from datetime import timedelta
from zoneinfo import ZoneInfo

import psycopg
from django import db
from django.db import connection, models
from django.utils.translation import gettext_lazy as _

from .choices import (
    HydrologicalMeasurementType,
    HydrologicalMetricName,
    MeteorologicalMeasurementType,
    MeteorologicalMetricName,
    MetricUnit,
    NormType,
)
from .managers import DischargeNormQuerySet, HydrologicalMetricQuerySet, MeteorologicalMetricQuerySet
from ..utils.datetime_helper import SmartDatetime

ESTIMATIONS_TABLE_MAP = {
    HydrologicalMetricName.WATER_LEVEL_DAILY_AVERAGE: "estimations_water_level_daily_average",
    HydrologicalMetricName.WATER_DISCHARGE_DAILY: "estimations_water_discharge_daily",
    HydrologicalMetricName.WATER_DISCHARGE_DAILY_AVERAGE: "estimations_water_discharge_daily_average",
    HydrologicalMetricName.WATER_DISCHARGE_FIVEDAY_AVERAGE: "estimations_water_discharge_fiveday_average",
    HydrologicalMetricName.WATER_DISCHARGE_DECADE_AVERAGE: "estimations_water_discharge_decade_average",
}


class HydrologicalMetric(models.Model):
    timestamp_local = models.DateTimeField(primary_key=True, verbose_name=_("Timestamp local"))
    timestamp = models.DateTimeField(verbose_name=_("Timestamp UTC"))
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
    value_code = models.IntegerField(verbose_name=_("Value code"), blank=True, null=True)

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

    def save(self, upsert=True, refresh_view=True, **kwargs) -> None:
        if self.timestamp_local is None and self.timestamp is not None:
            self.timestamp_local = SmartDatetime(self.timestamp, self.station, local=False).local.replace(tzinfo=ZoneInfo('UTC'))
        if self.timestamp_local is not None and self.timestamp is None:
            self.timestamp = SmartDatetime(self.timestamp_local, self.station, local=True).utc
            self.timestamp_local = self.timestamp_local.replace(tzinfo=ZoneInfo('UTC'))
        min_value = self.min_value if self.min_value is not None else "NULL"
        max_value = self.max_value if self.max_value is not None else "NULL"
        avg_value = self.avg_value if self.avg_value is not None else "NULL"
        value_code = self.value_code if self.value_code is not None else "NULL"

        sql_query_insert = f"""
            INSERT INTO metrics_hydrologicalmetric
            (timestamp_local, station_id, metric_name, value_type, sensor_identifier, timestamp, min_value, avg_value, max_value,
            unit, sensor_type, value_code)
            VALUES ('{self.timestamp_local}', {self.station_id}, '{self.metric_name}', '{self.value_type}', '{self.sensor_identifier}', '{self.timestamp}', {min_value},
            {avg_value}, {max_value}, '{self.unit}', '{self.sensor_type}', {value_code});
            """

        sql_query_upsert = f"""
            INSERT INTO metrics_hydrologicalmetric (timestamp_local, station_id, metric_name, value_type, sensor_identifier, timestamp, min_value, avg_value, max_value, unit, sensor_type, value_code)
            VALUES ('{self.timestamp_local}', {self.station_id}, '{self.metric_name}', '{self.value_type}', '{self.sensor_identifier}',  '{self.timestamp}', {min_value},
            {avg_value}, {max_value}, '{self.unit}', '{self.sensor_type}', {value_code})
            ON CONFLICT (timestamp_local, station_id, metric_name, value_type, sensor_identifier)
            DO UPDATE
            SET min_value = EXCLUDED.min_value,
                avg_value = EXCLUDED.avg_value,
                max_value = EXCLUDED.max_value,
                unit = EXCLUDED.unit,
                sensor_type = EXCLUDED.sensor_type;
        """

        try:  # TODO this is horrible, the metrics test factory only transactional block, need to find a better way
            if connection.client.connection.settings_dict["NAME"] == "test_sapphire_backend":
                conn = connection
            else:
                conn = psycopg.connect(self.conn_string, autocommit=True)
            with conn.cursor() as cursor:
                if upsert:
                    cursor.execute(sql_query_upsert)
                else:
                    cursor.execute(sql_query_insert)
            if connection.client.connection.settings_dict["NAME"] != "test_sapphire_backend":
                conn.close()
        except db.utils.NotSupportedError as e:
            """
            Handle specific error. Timescale has this bug, hyper chunks should not have insert blockers.
            E.g.:
            invalid INSERT on the root table of hypertable "_hyper_1_104_chunk"
            HINT:  Make sure the TimescaleDB extension has been preloaded.
            """
            if 'invalid INSERT on the root table of hypertable "' in str(e):
                hyper_chunk_name = str(e).split('invalid INSERT on the root table of hypertable "')[1].split('"')[0]
                if hyper_chunk_name.startswith("_hyper") and hyper_chunk_name.endswith("_chunk"):
                    sql_query_remove_trigger = (
                        f"drop trigger ts_insert_blocker on _timescaledb_internal.{hyper_chunk_name}; "
                    )
                    conn = psycopg.connect(self.conn_string, autocommit=True)
                    with conn.cursor() as cursor:
                        cursor.execute(sql_query_remove_trigger)
                        logging.info(f"Removed unwanted ts_insert_blocker on {hyper_chunk_name}")
                        cursor.execute(sql_query_insert)
                    conn.close()
                else:
                    raise Exception(e)
            else:
                raise Exception(e)
        except Exception as e:
            raise Exception(e)
        finally:
            if (
                refresh_view
                and self.metric_name == HydrologicalMetricName.WATER_LEVEL_DAILY
                and self.value_type == HydrologicalMeasurementType.MANUAL
            ):
                self._refresh_view()

    @property
    def conn_string(self):
        CONN_STRING = (
            f"host={connection.client.connection.settings_dict['HOST']} "
            f"port={connection.client.connection.settings_dict['PORT']} "
            f"user={connection.client.connection.settings_dict['USER']} "
            f"password={connection.client.connection.settings_dict['PASSWORD']} "
            f"dbname={connection.client.connection.settings_dict['NAME']}"
        )
        return CONN_STRING

    def _refresh_view(self):
        # cannot be in the same transaction block so we ensure this by creating a new connection with autocommit
        start_date_str = self.timestamp.strftime("%Y-%m-%d")
        end_date_str = (self.timestamp + timedelta(days=1)).strftime("%Y-%m-%d")
        sql_refresh_view = f"CALL refresh_continuous_aggregate('estimations_water_level_daily_average', '{start_date_str}', '{end_date_str}');"
        conn = psycopg.connect(self.conn_string, autocommit=True)
        with conn.cursor() as cursor:
            cursor.execute(sql_refresh_view)
        conn.close()

    def select_first(self):  # TODO JUST TEMPORARY USAGE, NOT SERIOUS
        table_name = self._meta.db_table
        if self.value_type == HydrologicalMeasurementType.ESTIMATED:
            table_name = ESTIMATIONS_TABLE_MAP.get(self.metric_name, self._meta.db_table)

        sql_query_select = f"""
            SELECT min_value, avg_value, max_value, unit, sensor_type FROM {table_name} WHERE
            timestamp='{self.timestamp}' AND station_id={self.station_id} AND metric_name='{self.metric_name}'
            AND value_type='{self.value_type}' AND sensor_identifier='{self.sensor_identifier}';
            """
        with connection.cursor() as cursor:
            cursor.execute(sql_query_select)
            row = cursor.fetchone()
            if row is not None:
                self.min_value, self.avg_value, self.max_value, self.unit, self.sensor_type = row
                return self


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
        sql_query_insert = f"""
        INSERT INTO metrics_meteorologicalmetric (timestamp, station_id, metric_name, value, value_type, unit )
        VALUES ('{self.timestamp}'::timestamp, {self.station_id}, '{self.metric_name}', {self.value}, '{self.value_type}', '{self.unit}');
        """

        sql_query_upsert = f"""
    INSERT INTO metrics_meteorologicalmetric (timestamp, station_id, metric_name, value, value_type, unit)
    VALUES ('{self.timestamp}'::timestamp, {self.station_id}, '{self.metric_name}', {self.value}, '{self.value_type}', '{self.unit}')
    ON CONFLICT (timestamp, station_id, metric_name)
    DO UPDATE
    SET value = EXCLUDED.value,
        value_type = EXCLUDED.value_type,
        unit = EXCLUDED.unit;
        """

        with connection.cursor() as cursor:
            if upsert:
                cursor.execute(sql_query_upsert)
            else:
                cursor.execute(sql_query_insert)


class DischargeNorm(models.Model):
    station = models.ForeignKey(
        "stations.HydrologicalStation",
        to_field="uuid",
        verbose_name=_("Hydrological station"),
        on_delete=models.CASCADE,
    )
    ordinal_number = models.PositiveIntegerField(verbose_name=_("Ordinal number"))
    value = models.DecimalField(verbose_name=_("Value"), max_digits=10, decimal_places=5)
    norm_type = models.CharField(
        verbose_name=_("Norm type"), choices=NormType, default=NormType.DECADAL, max_length=20
    )

    objects = DischargeNormQuerySet.as_manager()

    class Meta:
        verbose_name = _("Discharge norm")
        verbose_name_plural = _("Discharge norms")
        ordering = ["ordinal_number"]
        constraints = [
            models.UniqueConstraint("station", "ordinal_number", "norm_type", name="discharge_norm_unique_cn")
        ]
        indexes = [models.Index("norm_type", name="norm_type_idx")]

    def __str__(self):
        return f"{self.station.name} {self.norm_type} #{self.ordinal_number} - {self.value}"
