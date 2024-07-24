from django.conf import settings
from ieasyreports.core.tags import Tag

station_code = Tag(
    "SITE_CODE",
    lambda obj, **kwargs: obj.station_code,
    description="Site code",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
    data=True,
)
station_name = Tag(
    "SITE_NAME",
    lambda obj, **kwargs: obj.name,
    description="Site name",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
    data=True,
)
station_region = Tag(
    "SITE_REGION",
    lambda obj, **kwargs: obj.site.region.name,
    description="Site region",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
    data=True,
    header=True,
)
station_basin = Tag(
    "SITE_BASIN",
    lambda obj, **kwargs: obj.site.basin.name,
    description="Site basin",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
    data=True,
    header=True,
)
discharge_level_alarm = Tag(
    "DISCHARGE_MAX",
    lambda obj, **kwargs: obj.discharge_level_alarm or "-",
    description="Dangerous level of discharge",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
    data=True,
)
historical_minimum = Tag(
    "HISTORICAL_MINIMUM",
    lambda obj, **kwargs: obj.historical_discharge_minimum or "-",
    description="Historical minimum discharge value",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
    data=True,
)
historical_maximum = Tag(
    "HISTORICAL_MAXIMUM",
    lambda obj, **kwargs: obj.historical_discharge_maximum or "-",
    description="Historical maximum discharge value",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
    data=True,
)
