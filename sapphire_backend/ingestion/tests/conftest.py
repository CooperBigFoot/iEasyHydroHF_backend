import os
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from sapphire_backend.ingestion.models import FileState
from sapphire_backend.stations.models import HydrologicalStation
from sapphire_backend.stations.tests.factories import HydrologicalStationFactory, SiteFactory


@pytest.fixture
def filestate_zks_14_07_downloaded():
    filename = "imomo14_07_2024_09-00-03"
    local_path = os.path.join(Path(__file__).parent, "data", "zks", f"{filename}")

    fs = FileState(local_path=local_path,
                   remote_path=f"/manual/{filename}",
                   ingester_name="imomo_zks",
                   filename=filename,
                   state=FileState.States.DOWNLOADED
                   )
    fs.save()
    return fs


@pytest.fixture
def filestate_xml_20240131_downloaded():
    filename = "DATA_16000_20240131120000.xml.part"
    local_path = os.path.join(Path(__file__).parent, "data", "xml", f"{filename}")

    fs = FileState(local_path=local_path,
                   remote_path=f"/stream1/{filename}",
                   ingester_name="imomo_auto",
                   filename=filename,
                   state=FileState.States.DOWNLOADED
                   )
    fs.save()
    return fs


@pytest.fixture
def sites_zks_kyrgyz(organization_kyrgyz):
    return [SiteFactory(country="Kyrgyzstan", organization=organization_kyrgyz, timezone=ZoneInfo("Asia/Bishkek")) for i
            in range(6)]


@pytest.fixture
def hydro_stations_zks_kyrgyz(organization_kyrgyz, sites_zks_kyrgyz):
    # create manual hydro stations with code range 15000 - 15005
    return [HydrologicalStationFactory(station_code=str(station_code), site=site,
                                       station_type=HydrologicalStation.StationType.MANUAL) for station_code, site in
            enumerate(sites_zks_kyrgyz, 15000)]


@pytest.fixture
def hydro_stations_auto_kyrgyz(organization_kyrgyz, sites_zks_kyrgyz):
    # create auto hydro stations with code range 15000 - 15005
    return [HydrologicalStationFactory(station_code=str(station_code), site=site,
                                       station_type=HydrologicalStation.StationType.AUTOMATIC) for station_code, site in
            enumerate(sites_zks_kyrgyz, 15000)]
