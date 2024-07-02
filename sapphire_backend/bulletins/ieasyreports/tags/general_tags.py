from datetime import datetime as dt

from django.conf import settings
from ieasyreports.core.tags import Tag

today_tag = Tag(
    "TODAY",
    settings.IEASYREPORTS_CONF.data_manager_class.get_localized_date,
    description="Formatted value of the current date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
    value_fn_args={"date": dt.now()},
)

date_tag = Tag(
    "DATE",
    lambda target_date, **kwargs: settings.IEASYREPORTS_CONF.data_manager_class.get_localized_date(date=target_date),
    description="Formatted value of the given date",
    tag_settings=settings.IEASYREPORTS_TAG_CONF,
)
