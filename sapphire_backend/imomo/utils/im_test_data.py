"""The MIT License (MIT)

Copyright (c) 2014 Hydrosolutions GmbH

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""
import calendar
import datetime
import random

import pytz
from imomo.managers import DataValuesManager, DischargeModelsManager, SitesManager, UsersManager
from imomo.models import DischargeModels, StandardQualityControlLevels, StandardVariables, Users


def generate_data_set(imomo_init, username, site_data, discharge_model_data):
    user_manager = UsersManager(session=imomo_init.session)
    user = user_manager.query().filter(Users.username == username).one()
    user_manager.model = user
    timezone = pytz.timezone(user_manager.get_timezone())
    data_values_manager = DataValuesManager(session=imomo_init.session)
    site_manager = SitesManager(session=imomo_init.session)

    discharge_norm = [[{"discharge": random.randint(15, 25)} for _ in xrange(12)] for _ in xrange(3)]
    max_discharge = {"discharge": random.randint(40, 50)}

    site = site_manager.create(site_data, discharge_model_data, discharge_norm, max_discharge, user_manager)
    discharge_model_manager = DischargeModelsManager(session=imomo_init.session)
    discharge_model = (
        discharge_model_manager.query().filter(DischargeModels.model_name == discharge_model_data["modelName"]).one()
    )
    discharge_model_manager.model = discharge_model

    imomo_init.session.flush()

    start_date = datetime.date(2014, 8, 2)
    end_date = datetime.date(2014, 9, 5)
    previous_day_water_level_eight = None
    while start_date < end_date:
        water_level_eight = {
            "localDateTime": calendar.timegm(
                timezone.localize(
                    datetime.datetime(start_date.year, start_date.month, start_date.day, 8, 0, 0, 0)
                ).utctimetuple()
            ),
            "variableCode": StandardVariables.gauge_height_measurement.value,
            "qualityControlLevelCode": StandardQualityControlLevels.raw_data.value,
            "dataValue": random.randint(100, 160),
            "siteId": site.site_id,
            "censorCode": "nc",
        }
        water_level_twenty = {
            "localDateTime": calendar.timegm(
                timezone.localize(
                    datetime.datetime(start_date.year, start_date.month, start_date.day, 20, 0, 0, 0)
                    - datetime.timedelta(days=1)
                ).utctimetuple()
            ),
            "variableCode": StandardVariables.gauge_height_measurement.value,
            "qualityControlLevelCode": StandardQualityControlLevels.raw_data.value,
            "dataValue": random.randint(100, 160),
            "siteId": site.site_id,
            "censorCode": "nc",
        }
        average_water_level = {
            "localDateTime": calendar.timegm(
                timezone.localize(
                    datetime.datetime(start_date.year, start_date.month, start_date.day, 12, 0, 0, 0)
                    - datetime.timedelta(days=1)
                ).utctimetuple()
            ),
            "variableCode": StandardVariables.gauge_height_average_estimation.value,
            "qualityControlLevelCode": StandardQualityControlLevels.raw_data.value,
            "dataValue": (
                (
                    previous_day_water_level_eight["dataValue"]
                    if previous_day_water_level_eight
                    else water_level_twenty["dataValue"]
                )
                + water_level_twenty["dataValue"]
            )
            / 2,
            "siteId": site.site_id,
            "censorCode": "nc",
        }
        values = data_values_manager.store_daily_water_level(
            water_level_eight=water_level_eight,
            water_level_twenty=water_level_twenty,
            average_water_level=average_water_level,
            previous_day_water_level_eight=previous_day_water_level_eight,
            discharge_model_manager=discharge_model_manager,
            user_manager=user_manager,
        )

        if start_date.day == 10 or start_date.day == 20 or start_date.day == 30:
            water_level = {
                "localDateTime": calendar.timegm(
                    timezone.localize(
                        datetime.datetime(start_date.year, start_date.month, start_date.day, 14, 0, 0, 0)
                    ).utctimetuple()
                ),
                "variableCode": StandardVariables.gauge_height_measurement.value,
                "qualityControlLevelCode": StandardQualityControlLevels.raw_data.value,
                "dataValue": random.randint(100, 160),
                "siteId": site.site_id,
                "censorCode": "nc",
            }
            water_flow = {
                "localDateTime": water_level["localDateTime"],
                "variableCode": StandardVariables.discharge_measurement.value,
                "qualityControlLevelCode": StandardQualityControlLevels.raw_data.value,
                "dataValue": discharge_model_manager.calculate_discharge(water_level["dataValue"]),
                "siteId": site.site_id,
                "censorCode": "nc",
            }
            river_free_area = {
                "localDateTime": water_level["localDateTime"],
                "variableCode": StandardVariables.area_measurement.value,
                "qualityControlLevelCode": StandardQualityControlLevels.raw_data.value,
                "dataValue": random.randint(50, 100),
                "siteId": site.site_id,
                "censorCode": "nc",
            }
            maximum_depth = {
                "localDateTime": water_level["localDateTime"],
                "variableCode": StandardVariables.depth_measurement.value,
                "qualityControlLevelCode": StandardQualityControlLevels.raw_data.value,
                "dataValue": random.randint(180, 200),
                "siteId": site.site_id,
                "censorCode": "nc",
            }
            data_values_manager.store_discharge_data(
                water_flow=water_flow,
                water_level=water_level,
                river_free_area=river_free_area,
                maximum_depth=maximum_depth,
                user_manager=user_manager,
            )

        imomo_init.session.flush()
        previous_day_water_level_eight = {"valueId": values[2].value_id, "dataValue": values[2].data_value}

        start_date += datetime.timedelta(days=1)
    imomo_init.session.commit()


def generate_hydrosolutions_data_set():
    username = "diegob"
    site_data = {
        "siteCode": "000001",
        "siteName": "Test site 1",
        "latitude": "47.387574",
        "longitude": "8.538657",
        "state": "Switzerland",
        "county": "Zürich",
    }
    discharge_model_data = {
        "modelName": "Test discharge model A",
        "paramA": -20.0,
        "paramB": 1.5,
        "paramC": "0.003",
        "paramDeltaLevel": 0,
        "validFrom": 1410105199,
    }

    generate_data_set(username, site_data, discharge_model_data)

    site_data = {
        "siteCode": "000002",
        "siteName": "Test site 2",
        "latitude": "46.9500",
        "longitude": "7.4500",
        "state": "Switzerland",
        "county": "Bern",
    }
    discharge_model_data = {
        "modelName": "Test discharge model B",
        "paramA": -40.0,
        "paramB": 1.5,
        "paramC": "0.0025",
        "paramDeltaLevel": 0,
        "validFrom": 1410105199,
    }

    generate_data_set(username, site_data, discharge_model_data)

    site_data = {
        "siteCode": "000003",
        "siteName": "Test site 3",
        "latitude": "47.387574",
        "longitude": "8.538657",
        "state": "Switzerland",
        "county": "Zürich",
    }
    discharge_model_data = {
        "modelName": "Test discharge model C",
        "paramA": -15.0,
        "paramB": 1.6,
        "paramC": "0.004",
        "paramDeltaLevel": 0,
        "validFrom": 1410105199,
    }

    generate_data_set(username, site_data, discharge_model_data)

    site_data = {
        "siteCode": "000004",
        "siteName": "Test site 4",
        "latitude": "46.5198",
        "longitude": "6.6335",
        "state": "Switzerland",
        "county": "Lausanne",
    }
    discharge_model_data = {
        "modelName": "Test discharge model D",
        "paramA": -20.0,
        "paramB": 1.5,
        "paramC": "0.0023",
        "paramDeltaLevel": 0,
        "validFrom": 1410105199,
    }

    generate_data_set(username, site_data, discharge_model_data)

    site_data = {
        "siteCode": "000005",
        "siteName": "Test site 5",
        "latitude": "46.5198",
        "longitude": "6.6335",
        "state": "Switzerland",
        "county": "Lausanne",
    }
    discharge_model_data = {
        "modelName": "Test discharge model E",
        "paramA": -22.0,
        "paramB": 1.4,
        "paramC": "0.005",
        "paramDeltaLevel": 0,
        "validFrom": 1410105199,
    }

    generate_data_set(username, site_data, discharge_model_data)
