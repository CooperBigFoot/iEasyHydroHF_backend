from datetime import datetime as dt

from django.conf import settings
from ieasyreports.core.tags import Tag

# station related tags
station_code = Tag(
    "SITE_CODE",
    lambda **kwargs: kwargs["obj"].station_code,
    description="Site code",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
station_name = Tag(
    "SITE_NAME",
    lambda **kwargs: kwargs["obj"].name,
    description="Site name",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
station_region = Tag(
    "SITE_REGION",
    lambda **kwargs: kwargs["obj"].site.region.name,
    description="Site region",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
station_basin = Tag(
    "SITE_BASIN",
    lambda **kwargs: kwargs["obj"].site.basin.name,
    description="Site basin",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
discharge_level_alarm = Tag(
    "DISCHARGE_LEVEL_ALARM",
    lambda **kwargs: kwargs["obj"].discharge_level_alarm or "-",
    description="Dangerous level of discharge",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
historical_minimum = Tag(
    "HISTORICAL_MINIMUM",
    lambda **kwargs: kwargs["obj"].historical_discharge_minimum or "-",
    description="Historical minimum discharge value",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
historical_maximum = Tag(
    "HISTORICAL_MAXIMUM",
    lambda **kwargs: kwargs["obj"].historical_discharge_maximum or "-",
    description="Historical maximum discharge value",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)

# daily water level values
water_level_morning = Tag(
    "WATER_LEVEL_MORNING",
    lambda **kwargs: settings.IEASYREPORTS_CONF.data_manager_class.get_daily_water_level(
        kwargs["context"]["station_ids"], kwargs["context"]["target_date"]
    ),
    description="Morning (8 AM at local time) water level measurement for the selected date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
water_level_morning_1 = Tag(
    "WATER_LEVEL_MORNING_1",
    lambda **kwargs: settings.IEASYREPORTS_CONF.data_manager_class.get_daily_water_level(
        kwargs["context"]["station_ids"], kwargs["context"]["target_date"]
    ),
    description="Morning (8 AM at local time) water level measurement for day before the selected day",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
water_level_morning_2 = Tag(
    "WATER_LEVEL_MORNING_2",
    lambda **kwargs: print(kwargs),
    description="Morning (8 AM at local time) water level measurement for 2 days before the selected day",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
water_level_morning_trend = Tag(
    "WATER_LEVEL_MORNING_TREND",
    lambda **kwargs: print(kwargs),
    description="Water level morning (8 AM at local time) trend: selected date - previous day value",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
water_level_evening = Tag(
    "WATER_LEVEL_EVENING",
    lambda **kwargs: settings.IEASYREPORTS_CONF.data_manager_class.get_daily_water_level(
        kwargs["context"]["station_ids"], kwargs["context"]["target_date"]
    ),
    description="Evening (8 PM at local time) water level measurement for the selected date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
water_level_evening_1 = Tag(
    "WATER_LEVEL_EVENING_1",
    lambda **kwargs: print(kwargs),
    description="Evening (8 PM at local time) water level measurement for day before the selected date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
water_level_evening_2 = Tag(
    "WATER_LEVEL_EVENING_2",
    lambda **kwargs: settings.IEASYREPORTS_CONF.data_manager_class.get_daily_water_level(
        kwargs["context"]["station_ids"], kwargs["context"]["target_date"]
    ),
    description="Evening (8 PM at local time) water level measurement for 2 days before the selected date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
water_level_evening_trend = Tag(
    "WATER_LEVEL_EVENING_TREND",
    lambda **kwargs: print(kwargs),
    description="Water level evening (8 PM at local time) trend: selected date - previous day value",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
water_level_daily = Tag(
    "WATER_LEVEL_DAILY",
    lambda **kwargs: print(kwargs),
    description="Water level daily average for the selected date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
water_level_daily_1 = Tag(
    "WATER_LEVEL_DAILY_1",
    lambda **kwargs: print(kwargs),
    description="Water level daily average for day before the selected date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
water_level_daily_2 = Tag(
    "WATER_LEVEL_DAILY_2",
    lambda **kwargs: print(kwargs),
    description="Water level daily average for 2 days before the selected date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
water_level_daily_trend = Tag(
    "WATER_LEVEL_DAILY_TREND",
    lambda **kwargs: print(kwargs),
    description="Water level daily trend: selected date - previous day value",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)

# general tags
today = Tag(
    "TODAY",
    settings.IEASYREPORTS_CONF.data_manager_class.get_localized_date,
    description="Formatted value of the current date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
    value_fn_args={"date": dt.now()},
)

date = Tag(
    "DATE",
    lambda **kwargs: settings.IEASYREPORTS_CONF.data_manager_class.get_localized_date(
        date=kwargs["context"]["target_date"]
    ),
    description="Formatted value of the given date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)

common_tags = [
    station_name,
    station_code,
    station_region,
    station_basin,
    today,
    date,
    water_level_morning,
    water_level_morning_1,
    water_level_evening_2,
    water_level_evening,
]

daily_tags = common_tags.copy()
decadal_tags = common_tags.copy()
