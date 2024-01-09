# -*- encoding: UTF-8 -*-
from enum import Enum


class Variables(Enum):
    gauge_height_daily_measurement = '0001'
    gauge_height_average_daily_measurement = '0002'
    gauge_height_average_daily_estimation = '0003'
    discharge_daily_measurement = '0004'
    discharge_daily_estimation = '0005'
    river_cross_section_area_measurement = '0006'
    maximum_depth_measurement = '0007'
    discharge_decade_average = '0008'
    discharge_maximum_recommendation = '0009'
    discharge_daily_average_estimation = '0010'
    ice_phenomena_observation = '0011'
    gauge_height_decadal_measurement = '0012'
    water_temperature_observation = '0013'
    air_temperature_observation = '0014'
    discharge_fiveday_average = '0015'
    temperature_decade_average = '0016'
    temperature_month_average = '0017'
    precipitation_decade_average = '0018'
    precipitation_month_average = '0019'
    discharge_decade_average_historical = '0020'


class VariableRelationships:

    daily_to_fiveday_map = {
        Variables.discharge_daily_average_estimation.value: Variables.discharge_fiveday_average.value,
    }

    fiveday_to_decade_map = {
        Variables.discharge_fiveday_average.value: Variables.discharge_decade_average.value,
    }

    decade_to_month_map = {
        Variables.temperature_decade_average.value: Variables.temperature_month_average.value,
        Variables.precipitation_decade_average.value: Variables.precipitation_month_average.value,
    }

    daily_average_variables = [
        Variables.gauge_height_average_daily_estimation.value,
        Variables.discharge_daily_average_estimation.value,
    ]

    fiveday_average_variables = [
        Variables.discharge_fiveday_average.value,
    ]

    decade_average_variables = [
        Variables.discharge_decade_average.value,
        Variables.temperature_decade_average.value,
        Variables.precipitation_decade_average.value,
    ]

    month_average_variables = [
        Variables.temperature_month_average.value,
        Variables.precipitation_month_average.value,
    ]

    @classmethod
    def get_variable_frequency(cls, variable_code):
        if variable_code in cls.daily_average_variables:
            return 'daily_average'
        elif variable_code in cls.fiveday_average_variables:
            return 'fiveday_average'
        elif variable_code in cls.decade_average_variables:
            return 'decade_average'
        elif variable_code in cls.month_average_variables:
            return 'month_average'
