import logging
# Configure SQLAlchemy connection to the old database
import math
import os
from datetime import datetime

import psycopg
from django.db import connection
# Import necessary libraries
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

from sapphire_backend.estimations.models import DischargeModel
from sapphire_backend.imomo.data_structs.standard_data import Variables
from sapphire_backend.imomo.old_models import Variable
from sapphire_backend.imomo.old_models.data_sources import Source as OldSource  # Import your old SQLAlchemy model
from sapphire_backend.imomo.old_models.discharge_models import DischargeModel as OldDischargeModel
from sapphire_backend.imomo.old_models.monitoring_site_locations import Site as OldSite
from sapphire_backend.metrics.choices import (
    HydrologicalMeasurementType,
    HydrologicalMetricName,
    MeteorologicalMeasurementType,
    MeteorologicalMetricName,
    MetricUnit,
    NormType
)
from sapphire_backend.metrics.models import HydrologicalMetric, MeteorologicalMetric, HydrologicalNorm

from sapphire_backend.organizations.models import Basin, Organization, Region
from sapphire_backend.metrics.utils.helpers import PentadDecadeHelper
from sapphire_backend.stations.models import (
    HydrologicalStation,
    MeteorologicalStation,
    Site,
    VirtualStation,
    VirtualStationAssociation,
)
from sapphire_backend.telegrams.models import TelegramStored, TelegramReceived, TelegramParserLog
from sapphire_backend.utils.datetime_helper import SmartDatetime

nan_count = 0

MAP_OLD_SOURCE_ID_TO_NEW_ORGANIZATION_OBJ = {}
MAP_OLD_SITE_CODE_TO_NEW_SITE_OBJ = {}


def migrate_organizations(old_session, target_organization: str = ""):
    old_data = old_session.query(OldSource).order_by(OldSource.id).all()
    if target_organization:
        old_data = [old for old in old_data if old.organization == target_organization]
    # Configure Django connection to the new database
    for old in tqdm(old_data, desc="Organizations"):
        if old.year_type == "hydro_year":
            year_type = Organization.YearType.HYDROLOGICAL
        else:
            year_type = Organization.YearType.CALENDAR
        if old.language == "ru":
            language = Organization.Language.RUSSIAN
        else:
            language = Organization.Language.ENGLISH
        new_record = Organization(
            name=old.organization,
            description=old.source_description or "",
            url=old.source_link or "",
            country=old.country,
            city=old.city,
            street_address=old.address,
            zip_code=old.zip_code,
            latitude=None,
            longitude=None,
            timezone=old.timezone,
            contact=old.contact_name,
            contact_phone=old.phone,
            year_type=year_type,
            language=language,
            is_active=True,
        )
        new_record.save()
        MAP_OLD_SOURCE_ID_TO_NEW_ORGANIZATION_OBJ[old.id] = new_record


def get_or_create_basin(basin_name: str, organization: Organization):
    # TODO maybe force lowercase for basin_name, there can be duplicates otherwise
    basin = Basin.objects.filter(name=basin_name).first()
    if basin is None:
        basin = Basin(name=basin_name, organization=organization)
        basin.save()
    return basin


def get_or_create_region(region_name: str, organization: Organization):
    region = Region.objects.filter(name=region_name).first()
    if region is None:
        region = Region(name=region_name, organization=organization)
        region.save()
    return region


def get_or_create_site(
    old_site_code_repr,
    organization: Organization,
    country,
    basin: Basin,
    region: Region,
    latitude,
    longitude,
    elevation,
    timezone=None,
):
    site = MAP_OLD_SITE_CODE_TO_NEW_SITE_OBJ.get(old_site_code_repr, None)
    if site is None:
        site = Site(
            organization=organization,
            country=country,
            basin=basin,
            region=region,
            latitude=latitude,
            longitude=longitude,
            timezone=None,
            elevation=elevation,
        )
        site.save()
        MAP_OLD_SITE_CODE_TO_NEW_SITE_OBJ[old_site_code_repr] = site
    return site


def get_metric_name_unit_type(variable: Variable):
    var_code = variable.variable_code
    if var_code == Variables.gauge_height_daily_measurement.value:  # 0001
        metric_name = HydrologicalMetricName.WATER_LEVEL_DAILY
        metric_unit = MetricUnit.WATER_LEVEL
        measurement_type = HydrologicalMeasurementType.MANUAL
    elif var_code == Variables.gauge_height_average_daily_measurement.value:  # 0002
        metric_name = HydrologicalMetricName.WATER_LEVEL_DAILY_AVERAGE
        metric_unit = MetricUnit.WATER_LEVEL
        measurement_type = HydrologicalMeasurementType.IMPORTED
    elif var_code == Variables.gauge_height_average_daily_estimation.value:  # 0003 #
        # TODO this one is not used anywhere (2016. last time) so it could be ignored
        metric_name = HydrologicalMetricName.WATER_LEVEL_DAILY_AVERAGE
        metric_unit = MetricUnit.WATER_LEVEL
        measurement_type = HydrologicalMeasurementType.IMPORTED
    elif var_code == Variables.discharge_daily_measurement.value:  # 0004
        metric_name = HydrologicalMetricName.WATER_DISCHARGE_DAILY
        metric_unit = MetricUnit.WATER_DISCHARGE
        measurement_type = HydrologicalMeasurementType.MANUAL
    elif var_code == Variables.discharge_daily_estimation.value:  # 0005
        metric_name = HydrologicalMetricName.WATER_DISCHARGE_DAILY
        metric_unit = MetricUnit.WATER_DISCHARGE
        measurement_type = HydrologicalMeasurementType.IMPORTED
    elif var_code == Variables.river_cross_section_area_measurement.value:  # 0006:
        metric_name = HydrologicalMetricName.RIVER_CROSS_SECTION_AREA
        metric_unit = MetricUnit.AREA
        measurement_type = HydrologicalMeasurementType.MANUAL
    elif var_code == Variables.maximum_depth_measurement.value:  # 0007:
        metric_name = HydrologicalMetricName.MAXIMUM_DEPTH
        metric_unit = MetricUnit.WATER_LEVEL
        measurement_type = HydrologicalMeasurementType.MANUAL
    elif var_code == Variables.discharge_decade_average.value:  # 0008
        metric_name = HydrologicalMetricName.WATER_DISCHARGE_DECADE_AVERAGE
        metric_unit = MetricUnit.WATER_DISCHARGE
        measurement_type = HydrologicalMeasurementType.IMPORTED
    elif var_code == Variables.discharge_maximum_recommendation.value:  # 0009:
        return "", "", ""  # this will be at HydroStation level WATER_DISCHARGE_MAXIMUM_RECOMMENDATION
    elif var_code == Variables.discharge_daily_average_estimation.value:  # 0010
        metric_name = HydrologicalMetricName.WATER_DISCHARGE_DAILY_AVERAGE
        metric_unit = MetricUnit.WATER_DISCHARGE
        measurement_type = HydrologicalMeasurementType.IMPORTED
    elif var_code == Variables.ice_phenomena_observation.value:  # "0011":
        metric_name = HydrologicalMetricName.ICE_PHENOMENA_OBSERVATION
        metric_unit = MetricUnit.ICE_PHENOMENA_OBSERVATION
        measurement_type = HydrologicalMeasurementType.MANUAL
    elif var_code == Variables.gauge_height_decadal_measurement.value:  # 0012
        metric_name = HydrologicalMetricName.WATER_LEVEL_DECADAL
        metric_unit = MetricUnit.WATER_LEVEL
        measurement_type = HydrologicalMeasurementType.MANUAL
    elif var_code == Variables.water_temperature_observation.value:  # 0013
        metric_name = HydrologicalMetricName.WATER_TEMPERATURE
        metric_unit = MetricUnit.TEMPERATURE
        measurement_type = HydrologicalMeasurementType.MANUAL
    elif var_code == Variables.air_temperature_observation.value:  # 0014
        metric_name = HydrologicalMetricName.AIR_TEMPERATURE
        metric_unit = MetricUnit.TEMPERATURE
        measurement_type = HydrologicalMeasurementType.MANUAL
    elif var_code == Variables.discharge_fiveday_average.value:  # 0015
        metric_name = HydrologicalMetricName.WATER_DISCHARGE_FIVEDAY_AVERAGE
        metric_unit = MetricUnit.WATER_DISCHARGE
        measurement_type = HydrologicalMeasurementType.IMPORTED
    elif var_code == Variables.temperature_decade_average.value:  # 0016
        metric_name = MeteorologicalMetricName.AIR_TEMPERATURE_DECADE_AVERAGE
        metric_unit = MetricUnit.TEMPERATURE
        measurement_type = MeteorologicalMeasurementType.MANUAL
    elif var_code == Variables.temperature_month_average.value:  # 0017
        metric_name = MeteorologicalMetricName.AIR_TEMPERATURE_MONTH_AVERAGE
        metric_unit = MetricUnit.TEMPERATURE
        measurement_type = MeteorologicalMeasurementType.MANUAL
    elif var_code == Variables.precipitation_decade_average.value:  # 0018
        metric_name = MeteorologicalMetricName.PRECIPITATION_DECADE_AVERAGE
        metric_unit = MetricUnit.PRECIPITATION
        measurement_type = MeteorologicalMeasurementType.MANUAL
    elif var_code == Variables.precipitation_month_average.value:  # 0019
        metric_name = MeteorologicalMetricName.PRECIPITATION_MONTH_AVERAGE
        metric_unit = MetricUnit.PRECIPITATION
        measurement_type = MeteorologicalMeasurementType.MANUAL
    elif var_code == Variables.discharge_decade_average_historical.value:  # 0020
        metric_name = HydrologicalMetricName.WATER_DISCHARGE_DECADE_AVERAGE_HISTORICAL
        metric_unit = MetricUnit.WATER_DISCHARGE
        measurement_type = HydrologicalMeasurementType.IMPORTED
    return metric_name, metric_unit, measurement_type


def migrate_sites_and_stations(old_session, target_organization: str = ""):
    """Migrate sites and stations, optionally filtered by organization"""
    query = old_session.query(OldSite).order_by(OldSite.id)

    if target_organization:
        query = query.join(OldSource).filter(OldSource.organization == target_organization)

    old_data = query.all()
    cnt_hydro = 0
    cnt_meteo = 0

    for old in tqdm(old_data, desc="Stations", position=0):
        organization = MAP_OLD_SOURCE_ID_TO_NEW_ORGANIZATION_OBJ[old.source_id]

        if old.site_type == "meteo":
            shared_hydro_station = old_session.query(OldSite).filter(OldSite.site_code == old.site_code_repr).first()
            if shared_hydro_station is not None:
                basin = get_or_create_basin(basin_name=shared_hydro_station.basin, organization=organization)
            else:
                basin = get_or_create_basin(basin_name=old.basin, organization=organization)
        else:
            basin = get_or_create_basin(basin_name=old.basin, organization=organization)
        site = get_or_create_site(
            old_site_code_repr=old.site_code_repr,
            organization=organization,
            country=old.country,
            basin=basin,
            region=get_or_create_region(region_name=old.region, organization=organization),
            latitude=old.latitude,
            longitude=old.longitude,
            timezone=None,
            elevation=old.elevation_m,
        )
        print(f"created site inside migrate_sites_and_stations: {site}")

        if old.site_type == "meteo":
            meteo_station = MeteorologicalStation(
                name=old.site_name,
                station_code=old.site_code_repr,
                site=site,
                description=old.comments or "",
                is_deleted=False,
            )
            meteo_station.save()
            cnt_meteo = cnt_meteo + 1
        elif old.site_type == "discharge":
            hydro_station = HydrologicalStation(
                name=old.site_name,
                station_code=old.site_code_repr,
                station_type=HydrologicalStation.StationType.MANUAL,
                site=site,
                description=old.comments or "",
                measurement_time_step=None,
                discharge_level_alarm=None,
                is_deleted=False,
            )
            print(f"instantiated hydro_station inside migrate_sites_and_stations: {hydro_station}")
            hydro_station.save()
            print(f"saved hydro_station inside migrate_sites_and_stations: {hydro_station}")
            cnt_hydro = cnt_hydro + 1

    logging.info(f"Meteo count: {cnt_meteo}, hydro count: {cnt_hydro}")


def migrate_virtual_stations(old_session, target_organization: str = ""):
    """Migrate virtual stations, optionally filtered by organization"""
    query = old_session.query(OldSite).filter(OldSite.is_virtual == True).order_by(OldSite.id)

    if target_organization:
        query = query.join(OldSource).filter(OldSource.organization == target_organization)

    old_virtual_stations = query.all()
    cnt_virtual = 0
    cnt_associations = 0

    for old in tqdm(old_virtual_stations, desc="Virtual stations", position=0):
        organization = MAP_OLD_SOURCE_ID_TO_NEW_ORGANIZATION_OBJ[old.source_id]
        virtual_station = VirtualStation(
            name=old.site_name,
            station_code=old.site_code_repr,
            country=old.country,
            organization=organization,
            latitude=old.latitude,
            longitude=old.longitude,
            timezone=None,
            elevation=old.elevation_m,
            basin=get_or_create_basin(basin_name=old.basin, organization=organization),
            region=get_or_create_region(region_name=old.region, organization=organization)
        )
        virtual_station.save()
        cnt_virtual += 1
        for association in old.aggregation_site_associations:
            weight = float(association.weighting)
            discharge_station_code = association.aggregation.site_code_repr
            try:
                hydro_station = HydrologicalStation.objects.get(
                    station_code=discharge_station_code, station_type=HydrologicalStation.StationType.MANUAL
                )
                virtual_station_association = VirtualStationAssociation.objects.create(
                    hydro_station=hydro_station,
                    virtual_station=virtual_station,
                    weight=weight
                )
                cnt_associations += 1
            except HydrologicalStation.DoesNotExist:
                logging.error(
                    f"Could not find Hydrological station with the code {discharge_station_code} to associate "
                    f"with the virtual station."
                )

    logging.info(f"Virtual count: {cnt_virtual}, associations count: {cnt_associations}")


def migrate_meteo_metrics(
    old_session,
    limiter: int,
    target_station: OldSite,
    start_date: datetime = None,
    end_date: datetime = None
):
    """Migrate meteorological metrics with optional date range filtering"""
    print("Hello from migrate_meteo_metrics")
    old_stations = old_session.query(OldSite).filter(OldSite.site_code == target_station.site_code)

    for old in tqdm(old_stations, desc="Meteo stations", position=0):
        meteo_station = MeteorologicalStation.objects.get(station_code=old.site_code_repr)

        # Build data values query with date filtering
        data_values = old.data_values
        print(f"data_values: {data_values}")
        if start_date:
            data_values = [dv for dv in data_values if dv.local_date_time >= start_date]
        if end_date:
            data_values = [dv for dv in data_values if dv.local_date_time <= end_date]
        if limiter:
            data_values = data_values[-limiter:]

        for data_row in tqdm(
            data_values, desc="Meteo metrics", position=1, leave=False
        ):
            data_value = data_row.data_value

            if data_value == -9999:
                # Skip empty/unused values
                continue

            if math.isnan(data_value):
                continue  # Skip NaN values

            smart_datetime = SmartDatetime(data_row.local_date_time, meteo_station, tz_included=False)
            metric_name, metric_unit, measurement_type = get_metric_name_unit_type(data_row.variable)

            new_meteo_metric = MeteorologicalMetric(
                timestamp_local=smart_datetime.local,
                value=data_value,
                value_type=measurement_type,
                metric_name=metric_name,
                unit=metric_unit,
                station=meteo_station,
            )
            new_meteo_metric.save()


def refresh_water_level_daily_average(start_date: str, end_date: str):
    logging.info('Refreshing CAGG view')
    CONN_STRING = (
        f"host={connection.client.connection.settings_dict['HOST']} "
        f"port={connection.client.connection.settings_dict['PORT']} "
        f"user={connection.client.connection.settings_dict['USER']} "
        f"password={connection.client.connection.settings_dict['PASSWORD']} "
        f"dbname={connection.client.connection.settings_dict['NAME']}"
    )
    sql_refresh_view = f"CALL refresh_continuous_aggregate('estimations_water_level_daily_average', '{start_date}', '{end_date}');"
    conn = psycopg.connect(CONN_STRING, autocommit=True)
    with conn.cursor() as cursor:
        cursor.execute(sql_refresh_view)
    conn.close()
    logging.info('Done.')


def parse_ice_phenomena(data_row):
    try:
        ice_phenomena_values = data_row.ice_phenomena_string.split('|')
    except AttributeError:
        # the ice phenomena is not stored inside the ice_phenomena_string, but inside the data value
        integer_part, fractional_part = str(data_row.data_value).split(".")
        code = int(integer_part)
        if fractional_part == '0':
            intensity = 0
        elif len(fractional_part) == 1:
            intensity = int(fractional_part) * 10
        else:
            intensity = int(fractional_part.rstrip('0'))
        ice_phenomena_values = [f"{code}:{intensity}"]

    return ice_phenomena_values


def migrate_hydro_metrics(
    old_session,
    limiter: int,
    target_station: OldSite,
    start_date: datetime = None,
    end_date: datetime = None
):
    print("Hello from migrate_hydro_metrics")
    old_stations = old_session.query(OldSite).filter(OldSite.site_code == target_station.site_code)
    global nan_count

    for old in tqdm(old_stations, desc="Hydro stations", position=0):
        hydro_station = HydrologicalStation.objects.get(
            station_code=old.site_code_repr,
            station_type=HydrologicalStation.StationType.MANUAL
        )
        station_decades = {}

        # Build data values query with date filtering
        data_values = old.data_values
        if start_date:
            data_values = [dv for dv in data_values if dv.local_date_time >= start_date]
        if end_date:
            data_values = [dv for dv in data_values if dv.local_date_time <= end_date]
        if limiter:
            data_values = data_values[-limiter:]

        for data_row in tqdm(data_values, desc="Hydro metrics", position=1, leave=False):
            smart_datetime = SmartDatetime(data_row.local_date_time, hydro_station, tz_included=False)
            timestamp_local = smart_datetime.local

            if data_row.variable.variable_code in [Variables.air_temperature_observation.value,
                                                   Variables.water_temperature_observation.value]:
                # ensure that for ATO and WTO from section 1 group 4 the timestamp is set to morning because the old database
                # was very inconsistent about this
                timestamp_local = smart_datetime.morning_local

            # exceptionally set the maximum discharge on the hydro station level, exclude from metrics
            data_value = data_row.data_value

            if data_row.variable.variable_code == Variables.discharge_maximum_recommendation.value:
                hydro_station.discharge_level_alarm = data_value
                hydro_station.save()
                continue

            if data_row.variable.variable_code == Variables.discharge_decade_average_historical.value:
                if data_value == -9999:
                    # empty value for some reason
                    continue

                decade = PentadDecadeHelper.calculate_decade_from_the_date_in_year(smart_datetime.local)
                if decade not in station_decades:
                    station_decades[decade] = [data_value]
                else:
                    station_decades[decade].append(data_value)

                # right now we're only preparing the data, we need to go over all the data values
                # to store every relevant value after which we average them and store to the HydrologicalNorm model
                continue

            metric_name, metric_unit, measurement_type = get_metric_name_unit_type(data_row.variable)

            if measurement_type == HydrologicalMeasurementType.IMPORTED and metric_name in [
                HydrologicalMetricName.WATER_LEVEL_DAILY_AVERAGE,
                HydrologicalMetricName.WATER_DISCHARGE_DAILY,
                HydrologicalMetricName.WATER_DISCHARGE_DECADE_AVERAGE,
                HydrologicalMetricName.WATER_DISCHARGE_DAILY_AVERAGE,
                HydrologicalMetricName.WATER_DISCHARGE_FIVEDAY_AVERAGE]:
                # These metrics are now replaced by estimation views and are calculated on demand, not stored
                continue

            if data_row.variable.variable_code == Variables.ice_phenomena_observation.value:
                ice_phenomena_values = parse_ice_phenomena(data_row)
                for code_intensity_pair in ice_phenomena_values:
                    values = code_intensity_pair.split(':')
                    code = int(values[0])
                    intensity = None if values[1] == 'nan' else int(float(values[1]))
                    ice_phenomena_metric = HydrologicalMetric(
                        timestamp_local=timestamp_local,
                        min_value=None,
                        avg_value=intensity or -1,
                        max_value=None,
                        unit=metric_unit,
                        metric_name=metric_name,
                        value_type=measurement_type,
                        station=hydro_station,
                        sensor_identifier="",
                        sensor_type="",
                        value_code=code
                    )
                    ice_phenomena_metric.save(refresh_view=False)

                # metrics saved so we continue to the next one
                continue

            if data_row.variable.variable_code == Variables.gauge_height_average_daily_estimation.value:
                # this one is not used so it can be skipped
                continue

            if math.isnan(data_value):
                nan_count = nan_count + 1
                continue  # TODO skip NaN data value rows

            new_hydro_metric = HydrologicalMetric(
                timestamp_local=timestamp_local,
                min_value=None,
                avg_value=data_value,
                max_value=None,
                unit=metric_unit,
                value_type=measurement_type,
                metric_name=metric_name,
                station=hydro_station,
                sensor_identifier="",
                sensor_type="",
            )
            new_hydro_metric.save(refresh_view=False)

        for key, value in station_decades.items():
            if len(value) > 0:
                avg = sum(value) / len(value)
                HydrologicalNorm.objects.filter(
                    station=hydro_station,
                    ordinal_number=key,
                    norm_type=NormType.DECADAL
                ).delete()
                HydrologicalNorm.objects.create(
                    station=hydro_station,
                    ordinal_number=key,
                    value=avg,
                    norm_type=NormType.DECADAL
                )
    refresh_water_level_daily_average('2015-01-01', '2030-01-01')


def migrate_discharge_models(
    old_session,
    target_station: OldSite,
    start_date: datetime = None,
    end_date: datetime = None
):
    """Migrate discharge models with optional date range filtering"""
    print("Hello from migrate_discharge_models")
    query = old_session.query(OldDischargeModel).join(OldSite).filter(OldSite.site_code == target_station.site_code)

    if start_date:
        query = query.filter(OldDischargeModel.valid_from >= start_date)
    if end_date:
        query = query.filter(OldDischargeModel.valid_from <= end_date)

    old_discharge_models = query.all()

    for old in tqdm(old_discharge_models, desc="Discharge models", position=0):
        hydro_station = HydrologicalStation.objects.get(
            station_code=old.site.site_code_repr,
            station_type=HydrologicalStation.StationType.MANUAL
        )

        if old.valid_from is None:
            # when valid_from is None then it is initial discharge model
            # 2000-01-01 is sufficient as the beginning date of the initial model
            valid_from_local = SmartDatetime(
                datetime(2000, 1, 1, 0, 0, 0),
                hydro_station,
                tz_included=False
            ).day_beginning_local
        else:
            valid_from_local = SmartDatetime(
                old.valid_from,
                hydro_station,
                tz_included=False
            ).day_beginning_local

        # upsert
        DischargeModel.objects.filter(
            station_id=hydro_station.id,
            valid_from_local=valid_from_local
        ).delete()

        new_discharge_model = DischargeModel(
            name=old.model_name,
            param_a=old.param_a,
            param_b=old.param_b,
            param_c=old.param_c,
            valid_from_local=valid_from_local,
            station=hydro_station
        )
        new_discharge_model.save()


def cleanup_all():
    logging.info("Cleaning up discharge models")
    DischargeModel.objects.all().delete()
    logging.info("Cleaning up telegrams")
    TelegramStored.objects.all().delete()
    TelegramParserLog.objects.all().delete()
    TelegramReceived.objects.all().delete()
    logging.info("Cleaning up meteo metrics")
    MeteorologicalMetric.objects.all().delete()
    logging.info("Cleaning up discharge norms")
    HydrologicalNorm.objects.all().delete()
    logging.info("Cleaning up hydro metrics")
    HydrologicalMetric.objects.all().delete()
    logging.info("Cleaning up hydro stations")
    HydrologicalStation.objects.all().delete()
    logging.info("Cleaning up meteo stations")
    MeteorologicalStation.objects.all().delete()
    logging.info("Cleaning up virtual stations")
    VirtualStation.objects.all().delete()
    logging.info("Cleaning up sites")
    Site.objects.all().delete()
    logging.info("Cleaning up basins")
    Basin.objects.all().delete()
    logging.info("Cleaning up regions")
    Region.objects.all().delete()
    logging.info("Cleaning up organizations")
    Organization.objects.all().delete()
    logging.info("Done")

def get_old_db_url():
    return "postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}".format(
        user=os.environ.get("OLD_MIGRATION_DB_USERNAME", "hydrosolutions"),
        password=os.environ.get("OLD_MIGRATION_DB_PASSWORD", "hydrosolutions"),
        host=os.environ.get("OLD_MIGRATION_DB_HOST", "localhost"),
        port=os.environ.get("OLD_MIGRATION_DB_PORT", "5432"),
        db_name=os.environ.get("OLD_MIGRATION_DB_NAME", "hydrosolutions"),
    )

def migrate(
    skip_cleanup: bool,
    skip_structure: bool,
    target_station: str,
    target_organization: str,
    limiter: int,
    start_date: datetime = None,
    end_date: datetime = None
):
    """Main migration function with enhanced filtering options"""
    if not skip_cleanup:
        cleanup_all()
    else:
        logging.info(f"Skipped cleanup (--skip-cleanup = {skip_cleanup})")

    if limiter != 0:
        logging.info(f"Starting migrations in debugging mode (limiter = {limiter})")

    if start_date and end_date:
        logging.info(f"Migrating data between {start_date} and {end_date}")

    engine = create_engine(get_old_db_url())
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        if not skip_structure:
            migrate_organizations(session, target_organization)
            migrate_sites_and_stations(session, target_organization)
            migrate_virtual_stations(session, target_organization)
        else:
            logging.info(f"Skipped structure build (--skip-structure = {skip_structure})")

        # get target stations based on filters
        stations_query = session.query(OldSite)

        if target_organization:
            stations_query = stations_query.join(OldSource).filter(
                OldSource.organization == target_organization
            )
        if target_station:
            stations_query = stations_query.filter(OldSite.site_code == target_station)

        old_stations = stations_query.all()

        print("Hello from migrate")
        print(f"old_stations: {old_stations}")
        # migrate data for each station
        for old_station in tqdm(old_stations, desc="Migrating stations"):
            print(f"old_station: {old_station}")
            if old_station.site_type == "discharge":
                migrate_discharge_models(
                    session,
                    old_station,
                    start_date,
                    end_date
                )
                migrate_hydro_metrics(
                    session,
                    limiter,
                    old_station,
                    start_date,
                    end_date
                )
            elif old_station.site_type == "meteo":
                migrate_meteo_metrics(
                    session,
                    limiter,
                    old_station,
                    start_date,
                    end_date
                )
    finally:
        session.close()

    logging.info("Data migration completed successfully.")
