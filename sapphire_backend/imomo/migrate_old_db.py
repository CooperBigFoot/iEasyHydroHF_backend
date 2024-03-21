import logging
# Configure SQLAlchemy connection to the old database
import math
import zoneinfo
from datetime import datetime

from django.utils import timezone
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
)
from sapphire_backend.metrics.models import HydrologicalMetric, MeteorologicalMetric
from sapphire_backend.organizations.models import Basin, Organization, Region
from sapphire_backend.stations.models import HydrologicalStation, MeteorologicalStation, Site
from sapphire_backend.telegrams.models import Telegram
from sapphire_backend.utils.datetime_helper import SmartDatetime

nan_count = 0

MAP_OLD_SOURCE_ID_TO_NEW_ORGANIZATION_OBJ = {}
MAP_OLD_SITE_CODE_TO_NEW_SITE_OBJ = {}
LIMITER = 0  # FOR DEBUGGING PURPOSES, FOR PRODUCTION NEEDS TO BE 0


def migrate_organizations(old_session):
    old_data = old_session.query(OldSource).order_by(OldSource.id).all()
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
    elevation,  # TODO figure out
    timezone=None,  # TODO figure out
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
            timezone=None,  # TODO not available in old, figure out
            elevation=elevation,  # TODO not available in old,figure out
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
        measurement_type = MeteorologicalMeasurementType.IMPORTED
    elif var_code == Variables.temperature_month_average.value:  # 0017
        metric_name = MeteorologicalMetricName.AIR_TEMPERATURE_MONTH_AVERAGE
        metric_unit = MetricUnit.TEMPERATURE
        measurement_type = MeteorologicalMeasurementType.IMPORTED
    elif var_code == Variables.precipitation_decade_average.value:  # 0018
        metric_name = MeteorologicalMetricName.PRECIPITATION_DECADE_AVERAGE
        metric_unit = MetricUnit.PRECIPITATION
        measurement_type = MeteorologicalMeasurementType.IMPORTED
    elif var_code == Variables.precipitation_month_average.value:  # 0019
        metric_name = MeteorologicalMetricName.PRECIPITATION_MONTH_AVERAGE
        metric_unit = MetricUnit.PRECIPITATION
        measurement_type = MeteorologicalMeasurementType.IMPORTED
    elif var_code == Variables.discharge_decade_average_historical.value:  # 0020
        metric_name = HydrologicalMetricName.WATER_DISCHARGE_DECADE_AVERAGE_HISTORICAL
        metric_unit = MetricUnit.WATER_DISCHARGE
        measurement_type = HydrologicalMeasurementType.IMPORTED
    return metric_name, metric_unit, measurement_type


def migrate_sites_and_stations(old_session):
    old_data = old_session.query(OldSite).order_by(OldSite.id).all()
    cnt_hydro = 0
    cnt_meteo = 0
    cnt_virtual = 0
    for old in tqdm(old_data, desc="Stations", position=0):
        organization = MAP_OLD_SOURCE_ID_TO_NEW_ORGANIZATION_OBJ[old.source_id]

        # logic for basins, hydro stations basins are prioritized, so if there are both hydro and meteo
        # of the same code, the hydro basin will be created in DB and referenced by Site model
        # TODO ask them to standardize basin names according to the official list
        # so that we remove all the duplicates and redundant names
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
            timezone=None,  # TODO figure out
            elevation=old.elevation_m,  # TODO figure out
        )

        if old.site_type == "meteo":
            meteo_station = MeteorologicalStation(
                name=old.site_name,
                station_code=old.site_code_repr,  # TODO blank could be fine, or blank name in Site model
                site=site,
                description=old.comments or "",
                is_deleted=False,
            )
            meteo_station.save()
            cnt_meteo = cnt_meteo + 1
        elif old.site_type == "discharge":
            hydro_station = HydrologicalStation(
                name=old.site_name,
                station_code=old.site_code_repr,  # TODO blank could be fine, or blank name in Site model
                station_type=HydrologicalStation.StationType.MANUAL,
                site=site,
                description=old.comments or "",
                measurement_time_step=None,  # TODO figure out for manual stations
                discharge_level_alarm=None,
                historical_discharge_minimum=None,
                historical_discharge_maximum=None,
                decadal_discharge_norm=None,
                monthly_discharge_norm=None,
                is_deleted=False,
            )
            hydro_station.save()
            cnt_hydro = cnt_hydro + 1
        elif old.site_type == "virtual-discharge":
            # TODO what to do with virtual stations
            cnt_virtual = cnt_virtual + 1
    logging.info(f"Meteo count: {cnt_meteo}, hydro count: {cnt_hydro}, virtual: {cnt_virtual}")


def migrate_meteo_metrics(old_session):
    old_data = old_session.query(OldSite).all()
    meteo_stations = [station for station in old_data if station.site_type == "meteo"]
    for old in tqdm(meteo_stations, desc="Meteo stations", position=0):  # TODO limiter remove
        meteo_station = MeteorologicalStation.objects.get(station_code=old.site_code_repr)

        for data_row in tqdm(
            old.data_values[LIMITER:], desc="Meteo metrics", position=1, leave=False
        ):  # TODO remove limit
            naive_datetime = data_row.date_time_utc
            aware_datetime_utc = timezone.make_aware(
                naive_datetime, timezone=zoneinfo.ZoneInfo("UTC")
            )  # TODO double check this
            metric_name, metric_unit, measurement_type = get_metric_name_unit_type(data_row.variable)

            new_meteo_metric = MeteorologicalMetric(
                timestamp=aware_datetime_utc,  # TODO is local time needed?
                value=data_row.data_value,
                value_type=measurement_type,
                metric_name=metric_name,
                unit=metric_unit,
                station=meteo_station,
            )
            new_meteo_metric.save()


def migrate_hydro_metrics(old_session):
    global nan_count
    old_data = old_session.query(OldSite).all()
    hydro_stations = [station for station in old_data if station.site_type == "discharge"]
    for old in tqdm(hydro_stations, desc="Hydro stations", position=0):
        hydro_station = HydrologicalStation.objects.get(station_code=old.site_code_repr)
        for data_row in tqdm(
            old.data_values[LIMITER:], desc="Hydro metrics", position=1, leave=False
        ):  # TODO remove limit
            naive_datetime = data_row.date_time_utc
            aware_datetime_utc = timezone.make_aware(
                naive_datetime, timezone=zoneinfo.ZoneInfo("UTC")
            )  # TODO double check this

            # exceptionally set the maximum discharge on the hydro station level, exclude from metrics
            data_value = data_row.data_value

            if data_row.variable.variable_code == Variables.discharge_maximum_recommendation:
                hydro_station.discharge_level_alarm = data_value
                hydro_station.save()
                continue

            metric_name, metric_unit, measurement_type = get_metric_name_unit_type(data_row.variable)

            if data_row.variable.variable_code == Variables.ice_phenomena_observation:
                # TODO handle ice phenomena, currently skip
                continue

            if data_row.variable.variable_code == Variables.gauge_height_average_daily_estimation:
                # this one is not used so it can be skipped
                continue

            if math.isnan(data_value):
                nan_count = nan_count + 1
                continue  # TODO skip NaN data value rows

            new_hydro_metric = HydrologicalMetric(
                timestamp=aware_datetime_utc,  # TODO is local time needed?
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
            new_hydro_metric.save()

    print(f"Nan count {nan_count}")


def migrate_virtual_metrics(old_session):
    # TODO
    # old_data = old_session.query(OldSite).all()
    # virtual_stations = [station for station in old_data if station.site_type=='virtual-discharge']
    pass


def migrate_discharge_models(old_session):
    logging.info("Cleaning up discharge models")
    DischargeModel.objects.all().delete()
    old_discharge_models = old_session.query(OldDischargeModel).all()
    for old in tqdm(old_discharge_models, desc="Discharge models", position=0):
        hydro_station = HydrologicalStation.objects.get(station_code=old.site.site_code_repr)
        if old.valid_from is None:
            # when valid_from is None then it is initial discharge model
            # 2000-01-01 is sufficient as the beginning date of the initial model
            valid_from = SmartDatetime(datetime(2000, 1, 1, 0, 0, 0), hydro_station, local=True).day_beginning_utc
        else:
            valid_from = SmartDatetime(old.valid_from, hydro_station, local=True).day_beginning_utc

        new_discharge_model = DischargeModel(
            name=old.model_name,
            param_a=old.param_a,
            param_b=old.param_b,
            param_c=old.param_c,
            valid_from=valid_from,
            station=hydro_station
        )
        new_discharge_model.save()


def cleanup_all():
    logging.info("Cleaning up discharge models")
    DischargeModel.objects.all().delete()
    logging.info("Cleaning up telegrams")
    Telegram.objects.all().delete()
    logging.info("Cleaning up meteo metrics")
    MeteorologicalMetric.objects.all().delete()
    logging.info("Cleaning up hydro metrics")
    HydrologicalMetric.objects.all().delete()
    logging.info("Cleaning up hydro stations")
    HydrologicalStation.objects.all().delete()
    logging.info("Cleaning up meteo stations")
    MeteorologicalStation.objects.all().delete()
    logging.info("Cleaning up sites")
    Site.objects.all().delete()
    logging.info("Cleaning up basins")
    Basin.objects.all().delete()
    logging.info("Cleaning up regions")
    Region.objects.all().delete()
    logging.info("Cleaning up organizations")
    Organization.objects.all().delete()
    logging.info("Done")


def migrate():
    # now do the things that you want with your models here
    old_db_engine = create_engine(
        "postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}".format(
            user="hydrosolutions",
            password="hydrosolutions",
            host="localhost",
            port="5433",
            db_name="hydrosolutions",
        )
    )
    # Update with your old database connection string
    Session = sessionmaker(bind=old_db_engine)
    old_session = Session()
    # cleanup_all()
    if LIMITER != 0:
        logging.info(f"Starting migrations in debugging mode (LIMITER = {LIMITER})")
    # migrate_organizations(old_session)
    # migrate_sites_and_stations(old_session)
    migrate_discharge_models(old_session)
    # migrate_hydro_metrics(old_session)
    # migrate_meteo_metrics(old_session)
    # migrate_virtual_metrics(old_session)  # TODO
    old_session.close()
    print("Data migration completed successfully.")
