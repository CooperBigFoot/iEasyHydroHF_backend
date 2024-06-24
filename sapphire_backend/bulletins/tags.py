from datetime import datetime as dt

from django.conf import settings
from ieasyreports.core.tags import Tag

site_code = Tag("SITE_CODE", lambda station: station.station_code, tag_settings=settings.IEASYREPORTS_TAG_CONF)

site_name = Tag("SITE_NAME", lambda station: station.name, tag_settings=settings.IEASYREPORTS_TAG_CONF)

alarm_level = Tag(
    "ALARM_LEVEL", lambda station: station.discharge_alarm_level, tag_settings=settings.IEASYREPORTS_TAG_CONF
)

historical_min = Tag(
    "HISTORICAL_MIN", lambda station: station.historical_discharge_minimum, tag_settings=settings.IEASYREPORTS_TAG_CONF
)

historical_max = Tag(
    "HISTORICAL_MAX", lambda station: station.historical_discharge_maximum, tag_settings=settings.IEASYREPORTS_TAG_CONF
)

site_region = Tag("SITE_REGION", lambda station: station.site.region.name, tag_settings=settings.IEASYREPORTS_TAG_CONF)

today = Tag(
    "TODAY",
    settings.IEASYREPORTS_CONF.data_manager_class.get_localized_date,
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
    value_fn_args={"date": dt.now(), "language": "ky"},
)
