from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("measurements", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[(
                "ALTER TABLE public.measurement_measurements DROP CONSTRAINT measurement_measurements_pkey;\
                 ALTER TABLE public.measurement_measurements ADD CONSTRAINT measurement_measurements_pkey PRIMARY KEY (timestamp, metric, station_id);"
            )],
            reverse_sql=[(
                "ALTER TABLE public.measurement_measurements DROP CONSTRAINT measurement_measurements_tmp_pkey;\
                 ALTER TABLE public.measurement_measurements ADD CONSTRAINT measurement_measurements_pkey PRIMARY KEY (timestamp);"
            )]
        )
    ]
