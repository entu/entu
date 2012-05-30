from os import path

import tornado.ioloop
import tornado.locale
import tornado.web
import tornado.httpserver
import tornado.database
import tornado.options
from tornado.options import define, options

from db import *

define('debug',          help = 'run on debug mode',        type = str, default='False')
define('port',           help = 'run on the given port',    type = int, default=8000)
define('mysql_host',     help = 'mysql database host',      type = str)
define('mysql_database', help = 'mysql database name',      type = str)
define('mysql_user',     help = 'mysql database user',      type = str)
define('mysql_password', help = 'mysql database password',  type = str)

#: List of controllers to load.
controllers = [
    'auth',
    'entity',
    'public',
    'import',
]


class myApplication(tornado.web.Application):
    """
    Main Application handler. Imports controllers, settings, translations.

    """
    def __init__(self):
        handlers = []
        for controller in controllers:
            c = __import__ (controller, globals(), locals(), ['*'], -1)
            handlers.extend(c.handlers)

        settings = {
            'template_path':    path.join(path.dirname(__file__), '..', 'templates'),
            'static_path':      path.join(path.dirname(__file__), '..', 'static'),
            'debug':            True if str(options.debug).lower() == 'true' else False,
            'login_url':        '/auth/google',
            'xsrf_coocies':     True,
        }
        for preference in myDb().db.query('SELECT * FROM app_settings WHERE value IS NOT NULL;'):
            settings[preference.name] = preference.value

        tornado.web.Application.__init__(self, handlers, **settings)


if __name__ == '__main__':
    tornado.locale.load_translations(path.join(path.dirname(__file__), '..', 'translations'))
    tornado.options.parse_config_file(path.join(path.dirname(__file__), '..', 'conf', 'app.conf'))
    tornado.options.parse_command_line()
    tornado.httpserver.HTTPServer(myApplication(), xheaders=True).listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
