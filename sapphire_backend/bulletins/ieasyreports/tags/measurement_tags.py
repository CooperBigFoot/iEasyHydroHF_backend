from django.conf import settings
from ieasyreports.core.tags import Tag

from sapphire_backend.utils.daily_precipitation_mapper import DailyPrecipitationCodeMapper
from sapphire_backend.utils.ice_phenomena_mapper import IcePhenomenaCodeMapper
from sapphire_backend.utils.rounding import hydrological_round


def format_ice_phenomena(value):
    if not value or not isinstance(value, list):
        return None

    phenomena = []
    for item in value:
        if isinstance(item, dict):
            code = item.get("code")
            intensity = item.get("value")
            if code is not None:
                description = IcePhenomenaCodeMapper(code)._code_description_map.get(code, str(code))
                if intensity and intensity != -1:
                    percentage = int(round(float(intensity) * 10))
                    phenomena.append(f"{description} ({percentage}%)")
                else:
                    phenomena.append(description)

    return ", ".join(phenomena) if phenomena else None


def format_precipitation(value):
    if not value or not isinstance(value, list):
        return None

    for item in value:
        if isinstance(item, dict):
            code = item.get("code")
            value = item.get("value")
            if value is not None:
                if value == -1:
                    return None
                if code:
                    duration_desc = DailyPrecipitationCodeMapper(code).get_description()
                    formatted_value = str(hydrological_round(float(value)))
                    return f"{formatted_value} ({duration_desc})"
                return str(hydrological_round(float(value)))
    return None


ice_phenomena = Tag(
    "ICE_PHENOMENA",
    lambda **kwargs: format_ice_phenomena(
        settings.IEASYREPORTS_CONF.data_manager_class.get_ice_phenomena(
            kwargs["station_ids"], kwargs["obj"].id, kwargs["target_date"]
        )
    ),
    description="Ice phenomena observation for the current date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
    data=True,
)

precipitation = Tag(
    "PRECIPITATION",
    lambda **kwargs: format_precipitation(
        settings.IEASYREPORTS_CONF.data_manager_class.get_precipitation(
            kwargs["station_ids"], kwargs["obj"].id, kwargs["target_date"]
        )
    ),
    description="Precipitation measurement for the current date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
    data=True,
)
