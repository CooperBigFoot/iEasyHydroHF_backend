from django.conf import settings
from ieasyreports.core.tags import Tag

from sapphire_backend.utils.rounding import hydrological_round

ice_phenomena = Tag(
    "ICE_PHENOMENA",
    lambda **kwargs: settings.IEASYREPORTS_CONF.data_manager_class.get_ice_phenomena(
        kwargs["station_uuids"], kwargs["obj"].uuid, kwargs["target_date"]
    ),
    description="Ice phenomena observation for the current date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
    data=True,
)

precipitation = Tag(
    "PRECIPITATION",
    lambda **kwargs: settings.IEASYREPORTS_CONF.data_manager_class.get_precipitation(
        kwargs["station_uuids"], kwargs["obj"].uuid, kwargs["target_date"]
    ),
    description="Precipitation measurement for the current date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
    custom_number_format_fn=hydrological_round,
    data=True,
)
