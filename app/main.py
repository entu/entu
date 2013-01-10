from os import path

import tornado.ioloop
import tornado.locale
import tornado.web
import tornado.httpserver
import tornado.database
import tornado.options
from tornado.options import define, options

import logging


# Command line options
define('debug',          help = 'run on debug mode',        type = str, default='False')
define('port',           help = 'run on the given port',    type = int, default=8000)
define('mysql_host',     help = 'mysql database host',      type = str, default='localhost')
define('mysql_database', help = 'mysql database name',      type = str)
define('mysql_user',     help = 'mysql database user',      type = str)
define('mysql_password', help = 'mysql database password',  type = str)


# List of controllers to load.
controllers = [
    'auth',
    'entity',
    'public',
    'status',
    'action.ester',
    'action.csv_import',
    'api',
]


class MainPage(tornado.web.RequestHandler):
    """
    Redirects / to site's default path.

    """
    def get(self):
        self.require_setting('default_path', 'this application')
        self.redirect(self.settings['default_path'])


class PageNotFound(tornado.web.RequestHandler):
    """
    """
    def get(self, page=None):
        self.set_status(404)
        self.write('Page not found!')


class myApplication(tornado.web.Application):
    """
    Main Application handler. Imports controllers, settings, translations.

    """
    def __init__(self):
        handlers = [(r'/', MainPage)]
        for controller in controllers:
            c = __import__ (controller, globals(), locals(), ['*'], -1)
            handlers.extend(c.handlers)

            for h in c.handlers:
                logging.info('%s.py -> %s' % (controller, h[0]))
        handlers.append((r'(.*)', PageNotFound))

        settings = {
            'template_path':    path.join(path.dirname(__file__), '..', 'templates'),
            'static_path':      path.join(path.dirname(__file__), '..', 'static'),
            'debug':            True if str(options.debug).lower() == 'true' else False,
            'login_url':        '/auth/google',
            'xsrf_coocies':     True,
        }

        db = tornado.database.Connection(
            host        = options.mysql_host,
            database    = options.mysql_database,
            user        = options.mysql_user,
            password    = options.mysql_password,
        )
        for preference in db.query('SELECT keyname, value FROM app_settings WHERE value IS NOT NULL;'):
            settings[preference.keyname] = preference.value

        tornado.web.Application.__init__(self, handlers, **settings)


if __name__ == '__main__':
    tornado.options.enable_pretty_logging()
    tornado.locale.load_translations(path.join(path.dirname(__file__), '..', 'translations'))
    tornado.options.parse_command_line()
    tornado.httpserver.HTTPServer(myApplication(), xheaders=True).listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
