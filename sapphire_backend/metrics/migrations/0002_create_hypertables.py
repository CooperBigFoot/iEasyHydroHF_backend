from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("metrics", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[(
                "SELECT create_hypertable('public.metrics_waterdischarge', 'timestamp', chunk_time_interval => INTERVAL '1 day');\
                 SELECT create_hypertable('public.metrics_waterlevel', 'timestamp', chunk_time_interval => INTERVAL '1 day');\
                 SELECT create_hypertable('public.metrics_watervelocity', 'timestamp', chunk_time_interval => INTERVAL '1 day');\
                 SELECT create_hypertable('public.metrics_watertemperature', 'timestamp', chunk_time_interval => INTERVAL '1 day');\
                 SELECT create_hypertable('public.metrics_airtemperature', 'timestamp', chunk_time_interval => INTERVAL '1 day');"
            )],
            reverse_sql=[(
                "CREATE TABLE public.metrics_waterlevel_tmp (LIKE public.metrics_waterlevel INCLUDING ALL);"
                "INSERT INTO public.metrics_waterlevel_tmp (SELECT * FROM public.metrics_waterlevel);"
                "DROP TABLE public.metrics_waterlevel;"
                "ALTER TABLE public.metrics_waterlevel_tmp RENAME TO metrics_waterlevel;"

                "CREATE TABLE public.metrics_waterdischarge_tmp (LIKE public.metrics_waterdischarge INCLUDING ALL);"
                "INSERT INTO public.metrics_waterdischarge_tmp (SELECT * FROM public.metrics_waterdischarge);"
                "DROP TABLE public.metrics_waterdischarge;"
                "ALTER TABLE public.metrics_waterdischarge_tmp RENAME TO metrics_waterdischarge;"

                "CREATE TABLE public.metrics_watervelocity_tmp (LIKE public.metrics_watervelocity INCLUDING ALL);"
                "INSERT INTO public.metrics_watervelocity_tmp (SELECT * FROM public.metrics_watervelocity);"
                "DROP TABLE public.metrics_watervelocity;"
                "ALTER TABLE public.metrics_watervelocity_tmp RENAME TO metrics_watervelocity;"

                "CREATE TABLE public.metrics_watertemperature_tmp (LIKE public.metrics_watertemperature INCLUDING ALL);"
                "INSERT INTO public.metrics_watertemperature_tmp (SELECT * FROM public.metrics_watertemperature);"
                "DROP TABLE public.metrics_watertemperature;"
                "ALTER TABLE public.metrics_watertemperature_tmp RENAME TO metrics_watertemperature;"

                "CREATE TABLE public.metrics_airtemperature_tmp (LIKE public.metrics_airtemperature INCLUDING ALL);"
                "INSERT INTO public.metrics_airtemperature_tmp (SELECT * FROM public.metrics_airtemperature);"
                "DROP TABLE public.metrics_airtemperature;"
                "ALTER TABLE public.metrics_airtemperature_tmp RENAME TO metrics_airtemperature;"
            )]
        )
    ]
