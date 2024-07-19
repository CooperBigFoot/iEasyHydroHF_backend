import logging

from sapphire_backend.organizations.models import Organization
from sapphire_backend.stations.models import HydrologicalStation


def get_or_create_auto_station_by_code(station_code: str, organization: Organization) -> HydrologicalStation | None:
    """
    Get or create automatical hydro station in case there is already a manual station with the
    same station_code under organization. Currently it is expected that for all automatic stations there is already
    a corresponding manual station.
    """
    hydro_station_auto_obj = None
    try:
        hydro_station_auto_obj = HydrologicalStation.objects.get(
            station_code=station_code,
            station_type=HydrologicalStation.StationType.AUTOMATIC,
            site__organization=organization,
        )
    except HydrologicalStation.DoesNotExist:
        manual_station_same_code = HydrologicalStation.objects.filter(
            station_code=station_code,
            station_type=HydrologicalStation.StationType.MANUAL,
            site__organization=organization,
        ).first()
        if manual_station_same_code is not None:
            hydro_station_auto_obj = HydrologicalStation(
                name=manual_station_same_code.name,
                station_code=station_code,
                station_type=HydrologicalStation.StationType.AUTOMATIC,
                site=manual_station_same_code.site,
                description="",
                measurement_time_step=None,  # TODO is this needed ?
                discharge_level_alarm=manual_station_same_code.discharge_level_alarm,
                is_deleted=False,
            )
            hydro_station_auto_obj.save()
            logging.info(f"Created automatic hydro station from existing manual station code {station_code}")
    return hydro_station_auto_obj
