from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("metrics", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[(
                "ALTER TABLE public.metrics_metric \
                 DROP CONSTRAINT IF EXISTS metrics_metric_pkey,\
                 ADD PRIMARY KEY (timestamp, hydro_station_id, meteo_station_id, metric_name, sensor_identifier);"
            )]
        )
    ]
