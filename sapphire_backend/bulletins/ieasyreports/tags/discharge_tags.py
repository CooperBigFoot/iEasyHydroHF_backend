from django.conf import settings
from ieasyreports.core.tags import Tag

from .utils import get_trend, get_value

discharge_morning = Tag(
    "DISCHARGE_MORNING",
    lambda **kwargs: get_value(
        "discharge_daily", kwargs["station_ids"], kwargs["obj"].id, kwargs["target_date"], 0, "morning"
    ),
    description="Morning (8 AM at local time) water discharge estimation for the selected date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
discharge_morning_1 = Tag(
    "DISCHARGE_MORNING_1",
    lambda **kwargs: get_value(
        "discharge_daily", kwargs["station_ids"], kwargs["obj"].id, kwargs["target_date"], 1, "morning"
    ),
    description="Morning (8 AM at local time) water discharge estimation for day before the selected day",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
discharge_morning_2 = Tag(
    "DISCHARGE_MORNING_2",
    lambda **kwargs: get_value(
        "discharge_daily", kwargs["station_ids"], kwargs["obj"].id, kwargs["target_date"], 2, "morning"
    ),
    description="Morning (8 AM at local time) water discharge estimation for 2 days before the selected day",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
discharge_morning_trend = Tag(
    "DISCHARGE_MORNING_TREND",
    lambda **kwargs: get_trend(
        "discharge_daily",
        kwargs["station_ids"],
        kwargs["obj"].id,
        kwargs["target_date"],
        "morning",
    ),
    description="Water discharge morning (8 AM at local time) trend: selected date - previous day value",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
discharge_evening = Tag(
    "DISCHARGE_EVENING",
    lambda **kwargs: get_value(
        "discharge_daily", kwargs["station_ids"], kwargs["obj"].id, kwargs["target_date"], 0, "evening"
    ),
    description="Evening (8 PM at local time) water discharge estimation for the selected date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
discharge_evening_1 = Tag(
    "DISCHARGE_EVENING_1",
    lambda **kwargs: get_value(
        "discharge_daily", kwargs["station_ids"], kwargs["obj"].id, kwargs["target_date"], 1, "evening"
    ),
    description="Evening (8 PM at local time) water discharge estimation for day before the selected date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
discharge_evening_2 = Tag(
    "DISCHARGE_EVENING_2",
    lambda **kwargs: get_value(
        "discharge_daily", kwargs["station_ids"], kwargs["obj"].id, kwargs["target_date"], 2, "evening"
    ),
    description="Evening (8 PM at local time) water discharge estimation for 2 days before the selected date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
discharge_evening_trend = Tag(
    "DISCHARGE_EVENING_TREND",
    lambda **kwargs: get_trend(
        "discharge_daily",
        kwargs["station_ids"],
        kwargs["obj"].id,
        kwargs["target_date"],
        "evening",
    ),
    description="Water discharge evening (8 PM at local time) trend: selected date - previous day value",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
discharge_daily = Tag(
    "WATER_DISCHARGE_DAILY",
    lambda **kwargs: get_value("discharge_average", kwargs["station_ids"], kwargs["obj"].id, kwargs["target_date"], 0),
    description="Average daily discharge level estimation for the selected date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
discharge_daily_1 = Tag(
    "WATER_DISCHARGE_DAILY_1",
    lambda **kwargs: get_value("discharge_average", kwargs["station_ids"], kwargs["obj"].id, kwargs["target_date"], 1),
    description="Average daily discharge level estimation for the day before the selected date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
discharge_daily_2 = Tag(
    "WATER_DISCHARGE_DAILY_2",
    lambda **kwargs: get_value("discharge_average", kwargs["station_ids"], kwargs["obj"].id, kwargs["target_date"], 2),
    description="Average daily discharge level estimation for 2 days before the selected date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
discharge_daily_trend = Tag(
    "WATER_DISCHARGE_DAILY_TREND",
    lambda **kwargs: get_trend("discharge_daily", kwargs["station_ids"], kwargs["obj"].id, kwargs["target_date"]),
    description="Water discharge daily average estimation trend: selected date - previous day value",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
discharge_measurement = Tag(
    "DISCHARGE_MEASUREMENT",
    lambda **kwargs: get_value(
        "discharge_measurement", kwargs["station_ids"], kwargs["obj"].id, kwargs["target_date"], 0
    ),
    description="Discharge measurement (group 966) on the selected date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
discharge_fiveday = Tag(
    "DISCHARGE_FIVEDAY",
    lambda **kwargs: settings.IEASYREPORTS_CONF.data_manager_class.get_discharge_fiveday(
        kwargs["station_ids"], kwargs["obj"].id, kwargs["target_date"], 0
    ),
    description="Current 5-day period average discharge for the selected date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
discharge_fiveday_1 = Tag(
    "DISCHARGE_FIVEDAY_1",
    lambda **kwargs: settings.IEASYREPORTS_CONF.data_manager_class.get_discharge_fiveday(
        kwargs["station_ids"], kwargs["obj"].id, kwargs["target_date"], 5
    ),
    description="Previous 5-day period average discharge for the selected date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
discharge_decade = Tag(
    "DISCHARGE_DECADE",
    lambda **kwargs: settings.IEASYREPORTS_CONF.data_manager_class.get_discharge_decade(
        kwargs["station_ids"], kwargs["obj"].id, kwargs["target_date"], 0
    ),
    description="Current 10-day period average discharge for the selected date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
discharge_decade_1 = Tag(
    "DISCHARGE_DECADE_1",
    lambda **kwargs: settings.IEASYREPORTS_CONF.data_manager_class.get_discharge_decade(
        kwargs["station_ids"], kwargs["obj"].id, kwargs["target_date"], 10
    ),
    description="Previous 10-day period average discharge for the selected date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
discharge_norm = Tag(
    "DISCHARGE_NORM",
    lambda **kwargs: settings.IEASYREPORTS_CONF.data_manager_class.get_discharge_norm(
        kwargs["obj"].site.organization, kwargs["station_uuids"], kwargs["obj"].uuid, kwargs["target_date"]
    ),
    description="Decadal or monthly norm, depending on the settings on the organization level.",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
