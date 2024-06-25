from datetime import datetime as dt

from django.conf import settings
from ieasyreports.core.tags import Tag

site_code = Tag("SITE_CODE", lambda **kwargs: kwargs["obj"].station_code, tag_settings=settings.IEASYREPORTS_TAG_CONF)
site_name = Tag("SITE_NAME", lambda **kwargs: kwargs["obj"].name, tag_settings=settings.IEASYREPORTS_TAG_CONF)
site_region = Tag(
    "SITE_REGION", lambda **kwargs: kwargs["obj"].site.region.name, tag_settings=settings.IEASYREPORTS_TAG_CONF
)
site_basin = Tag(
    "SITE_BASIN", lambda **kwargs: kwargs["obj"].site.basin.name, tag_settings=settings.IEASYREPORTS_TAG_CONF
)

alarm_level = Tag(
    "ALARM_LEVEL",
    lambda **kwargs: kwargs["obj"].discharge_level_alarm or "-",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)

historical_min = Tag(
    "HISTORICAL_MIN",
    lambda **kwargs: kwargs["obj"].historical_discharge_minimum or "-",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)

historical_max = Tag(
    "HISTORICAL_MAX",
    lambda **kwargs: kwargs["obj"].historical_discharge_maximum or "-",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)


today = Tag(
    "TODAY",
    settings.IEASYREPORTS_CONF.data_manager_class.get_localized_date,
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
    value_fn_args={"date": dt.now()},
)
