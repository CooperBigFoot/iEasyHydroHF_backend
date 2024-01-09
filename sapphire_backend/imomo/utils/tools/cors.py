import cherrypy
from imomo import secrets


def preflight_request_tool(*args, **kwargs):
    """Attach headers to the response that allow CORS."""
    cherrypy.response.headers["Access-Control-Allow-Origin"] = secrets.ALLOWED_CORS_HOSTS


def handle_options(path, **kwargs):
    """Respond to an OPTIONS request with the appropriate headers."""
    cherrypy.response.headers["Access-Control-Allow-Origin"] = secrets.ALLOWED_CORS_HOSTS
    cherrypy.response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE"
    cherrypy.response.headers["Access-Control-Allow-Headers"] = cherrypy.request.headers.get(
        "Access-Control-Request-Headers", ""
    )
