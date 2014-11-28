from os import path

import torndb
import tornado.ioloop
import tornado.locale
import tornado.web
import tornado.httpserver
import tornado.options
from tornado.options import define, options

import yaml
import logging
import random
import string
import datetime, time


from main.helper import *
from main.db import *


# Command line options
define('debug',         help='run on debug mode',     type=str, default='False')
define('port',          help='run on the given port', type=int, default=8000)
define('host',          help='database host',         type=str)
define('database',      help='database name',         type=str)
define('user',          help='database user',         type=str)
define('password',      help='database password',     type=str)
define('customergroup', help='customergroup',         type=str, default=0)
define('secret',        help='secret key',            type=str, default='ABC123')


# List of controllers to load.
app_controllers = [
    'api.api',
    'api.api2',
    'entity.csv_import',
    'entity.entity',
    'importers.cmdi',
    'library.ester',
    'library.photo',
    'main.config',
    'main.status',
    'public.public',
    'update.update',
    'user.auth',
    'user.user',
]


class MainPage(myRequestHandler):
    """
    Redirects / to site's default path.

    """
    def get(self):
        self.redirect(self.app_settings('path'))


class PageNotFound(myRequestHandler):
    """
    """
    def get(self, page=None):
        self.missing()


class myApplication(tornado.web.Application):
    """
    Main Application handler. Imports controllers, settings, translations.

    """
    def __init__(self):
        # load settings
        settings = {
            'port':                 options.port,
            'debug':                True if str(options.debug).lower() == 'true' else False,
            'template_path':        path.join(path.dirname(__file__), '..', 'app'),
            'static_path':          path.join(path.dirname(__file__), '..', 'static'),
            'xsrf_coocies':         True,
            'cookie_secret':        'ess6ujukawreph98Et6q9ragAtuVevu3UPraqepr6maqaFreXch4huj6de3ezAcU',
            'login_url':            'https://entu.entu.ee/auth',
            'start_time':           time.time(),
            'request_count':        0,
            'request_time':         0,
            'slow_request_count':   0,
            'slow_request_time':    0,
            'slow_request_ms':      1000,
            'database-host':        options.host,
            'database-database':    options.database,
            'database-user':        options.user,
            'database-password':    options.password,
            'customergroup':        options.customergroup,
            'secret':               options.secret,
            'databases':            {},
        }

        # load handlers
        handlers = [(r'/', MainPage)]
        for controller in app_controllers:
            c = __import__ (controller, globals(), locals(), ['*'], -1)
            handlers.extend(c.handlers)
            for h in c.handlers:
                settings.setdefault('paths', {}).setdefault('%s.py' % controller, []).append(h[0])
        handlers.append((r'(.*)', PageNotFound))

        logging.warning('\n\n\n')
        logging.warning('Tornado %s started' % tornado.version)

        # init application
        # logging.debug('App settings:\n%s' % yaml.safe_dump(settings, default_flow_style=False, allow_unicode=True))
        tornado.web.Application.__init__(self, handlers, **settings)


if __name__ == '__main__':
    tornado.locale.load_translations(path.join(path.dirname(__file__), 'main', 'translation'))
    tornado.options.parse_command_line()
    tornado.httpserver.HTTPServer(myApplication(), xheaders=True, max_body_size=1024*1024*1024*5).listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
