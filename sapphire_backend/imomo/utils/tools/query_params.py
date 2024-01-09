import cherrypy
from imomo.utils.strings import camel_to_snake


def params_to_snake_case():
    """Function that allows changing all the request parameters from
    camelCase to snake_case.

    This should be attached as a tool before the
    handler to properly handle the keyword arguments in the handler classes
    which use snake_cases instead of the camelCase sent by the server.
    """
    original_params = cherrypy.request.params
    cherrypy.request.params = {}
    for key in original_params:
        cherrypy.request.params[camel_to_snake(key)] = original_params[key]
