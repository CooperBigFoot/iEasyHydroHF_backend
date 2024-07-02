from django.conf import settings
from ieasyreports.core.tags import Tag

from .utils import get_trend, get_value

water_level_morning = Tag(
    "WATER_LEVEL_MORNING",
    lambda **kwargs: get_value(
        "water_level_daily", kwargs["station_ids"], kwargs["obj"].id, kwargs["target_date"], 0, "morning"
    ),
    description="Morning (8 AM at local time) water level measurement for the selected date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
water_level_morning_1 = Tag(
    "WATER_LEVEL_MORNING_1",
    lambda **kwargs: get_value(
        "water_level_daily", kwargs["station_ids"], kwargs["obj"].id, kwargs["target_date"], 1, "morning"
    ),
    description="Morning (8 AM at local time) water level measurement for day before the selected day",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
water_level_morning_2 = Tag(
    "WATER_LEVEL_MORNING_2",
    lambda **kwargs: get_value(
        "water_level_daily", kwargs["station_ids"], kwargs["obj"].id, kwargs["target_date"], 2, "morning"
    ),
    description="Morning (8 AM at local time) water level measurement for 2 days before the selected day",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
water_level_morning_trend = Tag(
    "WATER_LEVEL_MORNING_TREND",
    lambda **kwargs: get_trend(
        "water_level_daily",
        kwargs["station_ids"],
        kwargs["obj"].id,
        kwargs["target_date"],
        "morning",
    ),
    description="Water level morning (8 AM at local time) trend: selected date - previous day value",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
water_level_evening = Tag(
    "WATER_LEVEL_EVENING",
    lambda **kwargs: get_value(
        "water_level_daily", kwargs["station_ids"], kwargs["obj"].id, kwargs["target_date"], 0, "evening"
    ),
    description="Evening (8 PM at local time) water level measurement for the selected date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
water_level_evening_1 = Tag(
    "WATER_LEVEL_EVENING_1",
    lambda **kwargs: get_value(
        "water_level_daily", kwargs["station_ids"], kwargs["obj"].id, kwargs["target_date"], 1, "evening"
    ),
    description="Evening (8 PM at local time) water level measurement for day before the selected date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
water_level_evening_2 = Tag(
    "WATER_LEVEL_EVENING_2",
    lambda **kwargs: get_value(
        "water_level_daily", kwargs["station_ids"], kwargs["obj"].id, kwargs["target_date"], 2, "evening"
    ),
    description="Evening (8 PM at local time) water level measurement for 2 days before the selected date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
water_level_evening_trend = Tag(
    "WATER_LEVEL_EVENING_TREND",
    lambda **kwargs: get_trend(
        "water_level_daily",
        kwargs["station_ids"],
        kwargs["obj"].id,
        kwargs["target_date"],
        "evening",
    ),
    description="Water level evening (8 PM at local time) trend: selected date - previous day value",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
water_level_daily = Tag(
    "WATER_LEVEL_DAILY",
    lambda **kwargs: get_value(
        "water_level_average",
        kwargs["station_ids"],
        kwargs["obj"].id,
        kwargs["target_date"],
        0,
    ),
    description="Average daily water level for the selected date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
water_level_daily_1 = Tag(
    "WATER_LEVEL_DAILY_1",
    lambda **kwargs: get_value(
        "water_level_average", kwargs["station_ids"], kwargs["obj"].id, kwargs["target_date"], 1
    ),
    description="Average daily water level for the day before the selected date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
water_level_daily_2 = Tag(
    "WATER_LEVEL_DAILY_2",
    lambda **kwargs: get_value(
        "water_level_average", kwargs["station_ids"], kwargs["obj"].id, kwargs["target_date"], 2
    ),
    description="Average daily water level for 2 days before the selected date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
water_level_daily_trend = Tag(
    "WATER_LEVEL_DAILY_TREND",
    lambda **kwargs: get_trend(
        "water_level_average",
        kwargs["station_ids"],
        kwargs["obj"].id,
        kwargs["target_date"],
    ),
    description="Water level daily average trend: selected date - previous day value",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
water_level_decadal_measurement = Tag(
    "WATER_LEVEL_DECADAL_MEASUREMENT",
    lambda **kwargs: get_value(
        "water_level_measurement", kwargs["station_ids"], kwargs["obj"].id, kwargs["target_date"], 0
    ),
    description="Water level decadal measurement (group 966) on the selected date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
