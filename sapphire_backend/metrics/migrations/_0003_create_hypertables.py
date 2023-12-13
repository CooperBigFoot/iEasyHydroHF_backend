from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("metrics", "0002_alter_pk"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[(
                "SELECT create_hypertable('public.metrics_metric', 'timestamp', chunk_time_interval => INTERVAL '1 day');\
                 ALTER TABLE public.metrics_metric SET (timescaledb.compress, timescaledb.compress_segmentby = 'hydro_station_id, meteo_station_id, sensor_identifier');\
                 SELECT add_compression_policy('public.metrics_metric', INTERVAL '1 month');"
            )]
        )
    ]
