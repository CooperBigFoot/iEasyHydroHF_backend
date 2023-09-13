from datetime import datetime

from django import template

register = template.Library()


@register.filter
def unlocalized_datetime(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return value
