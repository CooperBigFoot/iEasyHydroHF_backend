from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("metrics", "0002_alter_pk"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[(
                "SELECT create_hypertable('public.metrics_hydrologicalmetric', 'timestamp_local', chunk_time_interval => INTERVAL '6 month');\
                 SELECT create_hypertable('public.metrics_meteorologicalmetric', 'timestamp_local', chunk_time_interval => INTERVAL '120 month');"
                # \
                # ALTER TABLE public.metrics_hydrologicalmetric SET (timescaledb.compress, timescaledb.compress_segmentby = 'station_id, metric_name, sensor_identifier, value_type');\
                # ALTER TABLE public.metrics_meteorologicalmetric SET (timescaledb.compress, timescaledb.compress_segmentby = 'station_id, metric_name');\
                # SELECT add_compression_policy('public.metrics_hydrologicalmetric', INTERVAL '1 month');\
                # SELECT add_compression_policy('public.metrics_meteorologicalmetric', INTERVAL '1 month');"
            )],
            reverse_sql=[]
        )
    ]
