from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("measurements", "0002_alter_primary_key"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[(
                "SELECT create_hypertable('public.measurement_measurements', 'timestamp', chunk_time_interval => INTERVAL '1 day')"
            )],
            reverse_sql=[(
                "CREATE TABLE public.measurement_measurements_tmp (LIKE public.measurement_measurements INCLUDING ALL);\
                 INSERT INTO public.measurement_measurements_tmp (SELECT * FROM public.measurement_measurements);\
                 DROP TABLE public.measurement_measurements;\
                 ALTER TABLE public.measurement_measurements_tmp RENAME TO measurement_measurements"
            )]
        )
    ]
