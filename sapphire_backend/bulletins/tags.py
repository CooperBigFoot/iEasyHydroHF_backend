from django.conf import settings
from ieasyreports.core.tags import Tag

site_code = Tag("SITE_CODE", lambda station: station.station_code, tag_settings=settings.IEASYREPORTS_TAG_CONF)

site_name = Tag("SITE_CODE", lambda station: station.name, tag_settings=settings.IEASYREPORTS_TAG_CONF)

site_basin = Tag("SITE_BASIN", lambda station: station.site.basin.name, tag_settings=settings.IEASYREPORTS_TAG_CONF)

site_region = Tag("SITE_REGION", lambda station: station.site.region.name, tag_settings=settings.IEASYREPORTS_TAG_CONF)

today = Tag(
    "TODAY",
    settings.IEASYREPORTS_CONF.data_manager_class.get_localized_date,
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
