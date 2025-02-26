from .discharge_tags import (
    discharge_daily,
    discharge_daily_1,
    discharge_daily_2,
    discharge_daily_trend,
    discharge_decade,
    discharge_decade_1,
    discharge_evening,
    discharge_evening_1,
    discharge_evening_2,
    discharge_evening_trend,
    discharge_fiveday,
    discharge_fiveday_1,
    discharge_measurement,
    discharge_morning,
    discharge_morning_1,
    discharge_morning_2,
    discharge_morning_trend,
    discharge_norm,
    pentad_discharge_norm,
)
from .general_tags import date_tag, today_tag
from .measurement_tags import (
    ice_phenomena,
    precipitation,
)
from .station_tags import (
    discharge_level_alarm,
    historical_maximum,
    historical_minimum,
    station_basin,
    station_basin_national,
    station_code,
    station_name,
    station_national_name,
    station_region,
    station_region_national,
)
from .water_level_tags import (
    water_level_daily,
    water_level_daily_1,
    water_level_daily_2,
    water_level_daily_trend,
    water_level_decadal_measurement,
    water_level_evening,
    water_level_evening_1,
    water_level_evening_2,
    water_level_evening_trend,
    water_level_morning,
    water_level_morning_1,
    water_level_morning_2,
    water_level_morning_trend,
)

discharge_tags = [
    discharge_morning,
    discharge_morning_1,
    discharge_morning_2,
    discharge_morning_trend,
    discharge_evening,
    discharge_evening_1,
    discharge_evening_2,
    discharge_evening_trend,
    discharge_daily,
    discharge_daily_1,
    discharge_daily_2,
    discharge_daily_trend,
    discharge_fiveday,
    discharge_fiveday_1,
    discharge_decade,
    discharge_decade_1,
    discharge_norm,
    pentad_discharge_norm,
    discharge_measurement,
]

general_tags = [date_tag, today_tag]

station_tags = [
    station_name,
    station_code,
    station_region,
    station_basin,
    station_national_name,
    station_region_national,
    station_basin_national,
    discharge_level_alarm,
    historical_minimum,
    historical_maximum,
]

water_level_tags = [
    water_level_morning,
    water_level_morning_1,
    water_level_morning_2,
    water_level_morning_trend,
    water_level_evening,
    water_level_evening_1,
    water_level_evening_2,
    water_level_evening_trend,
    water_level_daily,
    water_level_daily_1,
    water_level_daily_2,
    water_level_daily_trend,
    water_level_decadal_measurement,
]

measurement_tags = [
    ice_phenomena,
    precipitation,
]
