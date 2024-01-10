from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("metrics", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[(
                "ALTER TABLE public.metrics_hydrologicalmetric \
                 DROP CONSTRAINT IF EXISTS metrics_hydrologicalmetric_pkey,\
                 ADD PRIMARY KEY (timestamp, station_id, metric_name, value_type, sensor_identifier);\
                 ALTER TABLE public.metrics_meteorologicalmetric \
                 DROP CONSTRAINT IF EXISTS metrics_meteorologicalmetric_pkey,\
                 ADD PRIMARY KEY (timestamp, station_id, metric_name);"
            )]
        )
    ]
