import logging
from datetime import datetime, timedelta

import psycopg
from django import db
from django.db import connection, models
from django.utils.translation import gettext_lazy as _

from sapphire_backend.quality_control.choices import HistoryLogStationType
from sapphire_backend.quality_control.models import HistoryLogEntry
from sapphire_backend.utils.mixins.models import SourceTypeMixin

from ..stations.models import HydrologicalStation, MeteorologicalStation
from ..utils.datetime_helper import SmartDatetime
from .choices import (
    HydrologicalMeasurementType,
    HydrologicalMetricName,
    MeteorologicalMeasurementType,
    MeteorologicalMetricName,
    MeteorologicalNormMetric,
    MetricUnit,
)
from .managers import (
    HydrologicalMetricQuerySet,
    HydrologicalNormQuerySet,
    MeteorologicalMetricQuerySet,
    MeteorologicalNormQuerySet,
)
from .mixins import BaseHydroMetricMixin, MinMaxValueMixin, NormModelMixin, SensorInfoMixin


def resolve_timestamp_local_tz_pair(
    timestamp_local: datetime | None,
    timestamp: datetime | None,
    station: [HydrologicalStation | MeteorologicalStation],
) -> (datetime, datetime):
    if timestamp_local is None and timestamp is not None:
        timestamp_local = SmartDatetime(timestamp, station, tz_included=True).local
    if timestamp_local is not None and timestamp is None:
        timestamp = SmartDatetime(timestamp_local, station, tz_included=False).tz
    return timestamp_local, timestamp


class HydrologicalMetric(BaseHydroMetricMixin, MinMaxValueMixin, SensorInfoMixin, SourceTypeMixin, models.Model):
    timestamp = models.DateTimeField(verbose_name=_("Timestamp with timezone"))
    station = models.ForeignKey("stations.HydrologicalStation", verbose_name=_("Station"), on_delete=models.PROTECT)
    value_code = models.IntegerField(verbose_name=_("Value code"), blank=True, null=True)

    objects = HydrologicalMetricQuerySet.as_manager()

    class Meta:
        verbose_name = _("Hydrological metric")
        verbose_name_plural = _("Hydrological metrics")
        ordering = ["-timestamp_local"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timestamp_local, self.timestamp = resolve_timestamp_local_tz_pair(
            timestamp_local=self.timestamp_local, timestamp=self.timestamp, station=self.station
        )

    def __str__(self):
        return f"{self.metric_name}, {self.station.name} on {self.timestamp_local.strftime('%Y-%m-%d %H:%M:%S')}"

    @property
    def pk_fields(self):
        return {
            "timestamp_local": self.timestamp_local,
            "station_id": self.station_id,
            "metric_name": self.metric_name,
            "value_type": self.value_type,
            "sensor_identifier": self.sensor_identifier,
        }

    def get_existing_record(self):
        try:
            return self.__class__.objects.get(**self.pk_fields)
        except self.__class__.DoesNotExist:
            return None

    def delete(self, **kwargs):
        sql_query_delete = f"""
        DELETE FROM metrics_hydrologicalmetric WHERE
        timestamp_local = '{self.timestamp_local}' AND
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
        min_value = self.min_value if self.min_value is not None else "NULL"
        max_value = self.max_value if self.max_value is not None else "NULL"
        avg_value = self.avg_value if self.avg_value is not None else "NULL"
        value_code = self.value_code if self.value_code is not None else "NULL"

        sql_query_insert = f"""
            INSERT INTO metrics_hydrologicalmetric
            (timestamp_local, station_id, metric_name, value_type, sensor_identifier, timestamp, min_value, avg_value, max_value,
            unit, sensor_type, value_code, source_type, source_id)
            VALUES ('{self.timestamp_local}', {self.station_id}, '{self.metric_name}', '{self.value_type}', '{self.sensor_identifier}', '{self.timestamp}', {min_value},
            {avg_value}, {max_value}, '{self.unit}', '{self.sensor_type}', {value_code}, '{self.source_type}', {self.source_id});
            """

        sql_query_upsert = f"""
            INSERT INTO metrics_hydrologicalmetric (timestamp_local, station_id, metric_name, value_type, sensor_identifier, timestamp, min_value, avg_value, max_value, unit, sensor_type, value_code, source_type, source_id)
            VALUES ('{self.timestamp_local}', {self.station_id}, '{self.metric_name}', '{self.value_type}', '{self.sensor_identifier}',  '{self.timestamp}', {min_value},
            {avg_value}, {max_value}, '{self.unit}', '{self.sensor_type}', {value_code}, '{self.source_type}', {self.source_id})
            ON CONFLICT (timestamp_local, station_id, metric_name, value_type, sensor_identifier)
            DO UPDATE
            SET min_value = EXCLUDED.min_value,
                avg_value = EXCLUDED.avg_value,
                max_value = EXCLUDED.max_value,
                source_type = EXCLUDED.source_type,
                source_id = EXCLUDED.source_id,
                unit = EXCLUDED.unit,
                sensor_type = EXCLUDED.sensor_type,
                value_code = EXCLUDED.value_code;
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
                and self.value_type in [HydrologicalMeasurementType.MANUAL, HydrologicalMeasurementType.AUTOMATIC]
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
        start_date_str = self.timestamp_local.strftime("%Y-%m-%d")
        end_date_str = (self.timestamp_local + timedelta(days=1)).strftime("%Y-%m-%d")
        sql_refresh_view = f"CALL refresh_continuous_aggregate('estimations_water_level_daily_average', '{start_date_str}', '{end_date_str}');"
        conn = psycopg.connect(self.conn_string, autocommit=True)
        with conn.cursor() as cursor:
            cursor.execute(sql_refresh_view)
        conn.close()

    @property
    def history_logs(self):
        return HistoryLogEntry.objects.filter(**self.pk_fields, station_type=HistoryLogStationType.HYDRO)

    def create_log_entry(self, old, description: str = ""):
        log_entry_values = {
            "previous_source_type": old.source_type,
            "previous_source_id": old.source_id,
            "previous_value_code": old.value_code,
            "previous_value": old.avg_value,
            "description": description,
            "new_value": self.avg_value,
            "new_source_type": self.source_type,
            "new_source_id": self.source_id,
            "new_value_code": self.value_code,
            "station_type": HistoryLogStationType.HYDRO,
        }
        return HistoryLogEntry.objects.create(**self.pk_fields, **log_entry_values)


class MeteorologicalMetric(SourceTypeMixin, models.Model):
    timestamp_local = models.DateTimeField(primary_key=True, verbose_name=_("Timestamp local without timezone"))
    timestamp = models.DateTimeField(verbose_name=_("Timestamp with timezone"))
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
        ordering = ["-timestamp_local"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timestamp_local, self.timestamp = resolve_timestamp_local_tz_pair(
            timestamp_local=self.timestamp_local, timestamp=self.timestamp, station=self.station
        )

    def __str__(self):
        return f"{self.metric_name}, {self.station.name} on {self.timestamp_local.strftime('%Y-%m-%d %H:%M:%S')}"

    @property
    def pk_fields(self):
        return {
            "timestamp_local": self.timestamp_local,
            "station_id": self.station_id,
            "metric_name": self.metric_name,
        }

    def get_existing_record(self):
        try:
            return self.__class__.objects.get(**self.pk_fields)
        except self.__class__.DoesNotExist:
            return None

    @property
    def history_logs(self):
        return HistoryLogEntry.objects.filter(
            timestamp_local=self.timestamp_local,
            station_id=self.station_id,
            metric_name=self.metric_name,
            station_type=HistoryLogStationType.METEO,
        )

    def create_log_entry(self, old, description: str = ""):
        log_entry_values = {
            "previous_source_type": old.source_type,
            "previous_source_id": old.source_id,
            "previous_value": old.value,
            "description": description,
            "new_value": self.value,
            "new_source_type": self.source_type,
            "new_source_id": self.source_id,
            "station_type": HistoryLogStationType.METEO,
        }
        return HistoryLogEntry.objects.create(**self.pk_fields, **log_entry_values)

    def delete(self, **kwargs) -> None:
        sql_query_delete = f"""
        DELETE FROM metrics_meteorologicalmetric WHERE
        timestamp_local = '{self.timestamp_local}' AND
        station_id = {self.station_id} AND
        metric_name = '{self.metric_name}';"""
        with connection.cursor() as cursor:
            cursor.execute(sql_query_delete)

    def save(self, upsert=True, **kwargs) -> None:
        sql_query_insert = f"""
        INSERT INTO metrics_meteorologicalmetric (timestamp_local, station_id, metric_name, timestamp, value, value_type, unit, source_type, source_id )
        VALUES ('{self.timestamp_local}', {self.station_id}, '{self.metric_name}', '{self.timestamp}', {self.value}, '{self.value_type}', '{self.unit}', '{self.source_type}', {self.source_id});
        """

        sql_query_upsert = f"""
    INSERT INTO metrics_meteorologicalmetric (timestamp_local, station_id, metric_name, timestamp, value, value_type, unit, source_type, source_id)
    VALUES ('{self.timestamp_local}', {self.station_id}, '{self.metric_name}', '{self.timestamp}', {self.value}, '{self.value_type}', '{self.unit}', '{self.source_type}', {self.source_id})
    ON CONFLICT (timestamp_local, station_id, metric_name)
    DO UPDATE
    SET value = EXCLUDED.value,
        value_type = EXCLUDED.value_type,
        unit = EXCLUDED.unit,
        source_type = EXCLUDED.source_type,
        source_id = EXCLUDED.source_id;
        """

        with connection.cursor() as cursor:
            if upsert:
                cursor.execute(sql_query_upsert)
            else:
                cursor.execute(sql_query_insert)


class HydrologicalNorm(NormModelMixin, models.Model):
    station = models.ForeignKey(
        "stations.HydrologicalStation",
        to_field="uuid",
        verbose_name=_("Hydrological station"),
        on_delete=models.CASCADE,
    )

    objects = HydrologicalNormQuerySet.as_manager()

    class Meta:
        verbose_name = _("Discharge norm")
        verbose_name_plural = _("Discharge norms")
        ordering = ["ordinal_number"]
        constraints = [
            models.UniqueConstraint("station", "ordinal_number", "norm_type", name="discharge_norm_unique_cn")
        ]
        indexes = [models.Index("norm_type", name="discharge_norm_type_idx")]

    def __str__(self):
        return f"Discharge norm {self.station.name} ({self.norm_type} - {self.ordinal_number})"


class MeteorologicalNorm(NormModelMixin, models.Model):
    station = models.ForeignKey(
        "stations.MeteorologicalStation",
        to_field="uuid",
        verbose_name=_("Meteorological station"),
        on_delete=models.CASCADE,
    )
    norm_metric = models.CharField(
        verbose_name=_("Norm type"),
        choices=MeteorologicalNormMetric,
        default=MeteorologicalNormMetric.PRECIPITATION,
        max_length=2,
    )

    objects = MeteorologicalNormQuerySet.as_manager()

    class Meta:
        verbose_name = _("Meteorological norm")
        verbose_name_plural = _("Meteorological norms")
        ordering = ["ordinal_number"]
        constraints = [
            models.UniqueConstraint(
                "station", "ordinal_number", "norm_type", "norm_metric", name="meteorological_norm_unique_cn"
            )
        ]
        indexes = [
            models.Index("norm_type", name="meteo_norm_type_idx"),
            models.Index("norm_metric", name="meteo_norm_metric_idx"),
        ]

    def __str__(self):
        return f"Meteo norm {self.station.name} ({self.norm_type}, {self.norm_metric} - {self.ordinal_number})"


class BulkDataHydroManual(models.Model):
    station = models.ForeignKey("stations.HydrologicalStation", on_delete=models.DO_NOTHING)
    timestamp_local = models.DateTimeField()
    water_level_daily = models.DecimalField(max_digits=10, decimal_places=3)
    water_level_daily_average = models.DecimalField(max_digits=10, decimal_places=3)
    discharge_measurement = models.DecimalField(max_digits=10, decimal_places=3)
    discharge_daily = models.DecimalField(max_digits=10, decimal_places=3)
    free_river_area = models.DecimalField(max_digits=10, decimal_places=3)
    decade_discharge = models.DecimalField(max_digits=10, decimal_places=3)
    discharge_daily_average = models.DecimalField(max_digits=10, decimal_places=3)
    ice_phenomena = models.CharField(max_length=20, blank=True)
    water_level_measurement = models.DecimalField(max_digits=10, decimal_places=3)
    fiveday_discharge = models.DecimalField(max_digits=10, decimal_places=3)
    air_temperature = models.DecimalField(max_digits=10, decimal_places=3)
    water_temperature = models.DecimalField(max_digits=10, decimal_places=3)
    precipitation_daily = models.CharField(max_length=20, blank=True)

    class Meta:
        managed = False
        db_table = "metrics_bulk_data_hydro_manual"


class BulkDataHydroAuto(models.Model):
    station = models.ForeignKey("stations.HydrologicalStation", on_delete=models.DO_NOTHING)
    timestamp_local = models.DateTimeField()
    water_level_daily_min = models.DecimalField(max_digits=10, decimal_places=3)
    water_level_daily_average = models.DecimalField(max_digits=10, decimal_places=3)
    water_level_daily_max = models.DecimalField(max_digits=10, decimal_places=3)
    air_temperature_min = models.DecimalField(max_digits=10, decimal_places=3)
    air_temperature_average = models.DecimalField(max_digits=10, decimal_places=3)
    air_temperature_max = models.DecimalField(max_digits=10, decimal_places=3)
    water_temperature_min = models.DecimalField(max_digits=10, decimal_places=3)
    water_temperature_average = models.DecimalField(max_digits=10, decimal_places=3)
    water_temperature_max = models.DecimalField(max_digits=10, decimal_places=3)
    discharge_daily_average = models.DecimalField(max_digits=10, decimal_places=3)
    fiveday_discharge = models.DecimalField(max_digits=10, decimal_places=3)
    decade_discharge = models.DecimalField(max_digits=10, decimal_places=3)

    class Meta:
        managed = False
        db_table = "metrics_bulk_data_hydro_auto"


class BulkDataVirtual(models.Model):
    station = models.ForeignKey("stations.VirtualStation", on_delete=models.DO_NOTHING)
    timestamp_local = models.DateTimeField()
    discharge_daily = models.DecimalField(max_digits=10, decimal_places=3)
    decade_discharge = models.DecimalField(max_digits=10, decimal_places=3)
    discharge_daily_average = models.DecimalField(max_digits=10, decimal_places=3)
    fiveday_discharge = models.DecimalField(max_digits=10, decimal_places=3)

    class Meta:
        managed = False
        db_table = "metrics_bulk_data_virtual"


class BulkDataMeteo(models.Model):
    station = models.ForeignKey("stations.MeteorologicalStation", on_delete=models.DO_NOTHING)
    timestamp_local = models.DateTimeField()
    air_temperature_decade_average = models.DecimalField(max_digits=10, decimal_places=3)
    air_temperature_month_average = models.DecimalField(max_digits=10, decimal_places=3)
    precipitation_decade_average = models.DecimalField(max_digits=10, decimal_places=3)
    precipitation_month_average = models.DecimalField(max_digits=10, decimal_places=3)

    class Meta:
        managed = False
        db_table = "metrics_bulk_data_meteo"
