from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("metrics", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[(
                "SELECT create_hypertable('public.metrics_water_discharge', 'timestamp', chunk_time_interval => INTERVAL '1 day');\
                 SELECT create_hypertable('public.metrics_water_level', 'timestamp', chunk_time_interval => INTERVAL '1 day');\
                 SELECT create_hypertable('public.metrics_water_velocity', 'timestamp', chunk_time_interval => INTERVAL '1 day');\
                 SELECT create_hypertable('public.metrics_water_temperature', 'timestamp', chunk_time_interval => INTERVAL '1 day');\
                 SELECT create_hypertable('public.metrics_air_temperature', 'timestamp', chunk_time_interval => INTERVAL '1 day');"
            )],
            reverse_sql=[(
                "CREATE TABLE public.metrics_water_level_tmp (LIKE public.metrics_water_level INCLUDING ALL);"
                "INSERT INTO public.metrics_water_level_tmp (SELECT * FROM public.metrics_water_level);"
                "DROP TABLE public.metrics_water_level;"
                "ALTER TABLE public.metrics_water_level_tmp RENAME TO metrics_water_level;"

                "CREATE TABLE public.metrics_water_discharge_tmp (LIKE public.metrics_water_discharge INCLUDING ALL);"
                "INSERT INTO public.metrics_water_discharge_tmp (SELECT * FROM public.metrics_water_discharge);"
                "DROP TABLE public.metrics_water_discharge;"
                "ALTER TABLE public.metrics_water_discharge_tmp RENAME TO metrics_water_discharge;"

                "CREATE TABLE public.metrics_water_velocity_tmp (LIKE public.metrics_water_velocity INCLUDING ALL);"
                "INSERT INTO public.metrics_water_velocity_tmp (SELECT * FROM public.metrics_water_velocity);"
                "DROP TABLE public.metrics_water_velocity;"
                "ALTER TABLE public.metrics_water_velocity_tmp RENAME TO metrics_water_velocity;"

                "CREATE TABLE public.metrics_water_temperature_tmp (LIKE public.metrics_water_temperature INCLUDING ALL);"
                "INSERT INTO public.metrics_water_temperature_tmp (SELECT * FROM public.metrics_water_temperature);"
                "DROP TABLE public.metrics_water_temperature;"
                "ALTER TABLE public.metrics_water_temperature_tmp RENAME TO metrics_water_temperature;"

                "CREATE TABLE public.metrics_air_temperature_tmp (LIKE public.metrics_air_temperature INCLUDING ALL);"
                "INSERT INTO public.metrics_air_temperature_tmp (SELECT * FROM public.metrics_air_temperature);"
                "DROP TABLE public.metrics_air_temperature;"
                "ALTER TABLE public.metrics_air_temperature_tmp RENAME TO metrics_air_temperature;"
            )]
        )
    ]
