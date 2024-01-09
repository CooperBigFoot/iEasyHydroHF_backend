# -*- encoding: UTF-8 -*-
import logging

import cherrypy
from cherrypy.lib import httputil
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from imomo import secrets


logger = logging.getLogger('hydromet')


class PostgreSQLTool(cherrypy.Tool):
    """Tool to attach a db connection to the request object.

    This allows the use of reusable connections among different requests with
    sessions scoped by request.
    """

    def __init__(self):
        cherrypy.Tool.__init__(self, 'on_start_resource',
                               self.bind_session,
                               priority=20)

    def _setup(self):
        cherrypy.Tool._setup(self)
        cherrypy.request.hooks.attach('on_end_resource',
                                      self.commit_transaction,
                                      priority=80)
        cherrypy.request.hooks.attach('after_error_response',
                                      self.rollback_transaction,
                                      priority=80)

    def bind_session(self):
        """Retrieves the session from the plugin and attaches it to the
        request.

        The session is retrieved by publishing the bind-session event and
        popping the output.
        """
        try:
            session = cherrypy.engine.publish('bind-session').pop()
        except IndexError:
            raise
        cherrypy.request.db = session

    def commit_transaction(self):
        """Issues a message to either commit or rollback the current session
        depending on the response's status code.

        The 'commit-session' message is published to the engine if the status
        code is between [200, 300), otherwise 'rollback-session' is emitted.
        Both messages are processed by the database plugin.
        """
        if not hasattr(cherrypy.request, 'db'):
            return
        cherrypy.request.db = None
        status_code, _, _ = httputil.valid_status(cherrypy.response.status)
        if status_code >= 200 and status_code < 300:
            cherrypy.engine.publish('commit-session')
        else:
            cherrypy.engine.publish('rollback-session')

    def rollback_transaction(self):
        """Issues a message to rollback the current session after an error.

        The 'rollback-session' message is published to the engine to be picked
        up by the database plugin.
        """
        if not hasattr(cherrypy.request, 'db'):
            return
        cherrypy.request.db = None
        cherrypy.engine.publish('rollback-session')


class DBContextManager(object):

    def __init__(self):
        self.engine = create_engine(
            'postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}'.format(
                user=secrets.DB_USER,
                password=secrets.DB_PASSWORD,
                host=secrets.DB_HOST,
                port=secrets.DB_PORT,
                db_name=secrets.DB_NAME,
            ), echo=secrets.DB_ECHO)

        self.session_maker = scoped_session(sessionmaker(bind=self.engine))

    def __enter__(self):
        self.session = self.session_maker()
        logger.info('DB connection created: {}'.format(id(self)))
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.engine.dispose()
        logger.info('DB connection closed: {}'.format(id(self)))
