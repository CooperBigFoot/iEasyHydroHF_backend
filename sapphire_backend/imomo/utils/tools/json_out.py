# -*- encoding: UTF-8 -*-
import calendar
import datetime
import json

import cherrypy


class ImomoEncoder(json.JSONEncoder):
    """Enhanced JSON encoder that supports some objects that appear in the
    system's models.

    Currently it can process datetime.datetime objects by converting them
    to a UNIX timestamp.
    """
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return calendar.timegm(obj.utctimetuple())
        return json.JSONEncoder.default(self, obj)


def json_handler(*args, **kwargs):
    """Modified JSON handler to include a custom JSON encoder."""
    value = cherrypy.serving.request._json_inner_handler(*args, **kwargs)
    return ImomoEncoder().iterencode(value)
