import gettext
import os

import cherrypy


def set_language_from_header():
    language = cherrypy.request.headers.get("Language")
    if language is not None:
        locales = os.environ.get("LOCALES_PATH", "locales")
        t = gettext.translation("messages", locales, languages=[language])
        t.install()
