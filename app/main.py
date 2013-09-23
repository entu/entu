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
define('debug', help='run on debug mode',     type=str, default='False')
define('port',  help='run on the given port', type=int, default=8000)


# List of controllers to load.
app_controllers = [
    'action.csv_import',
    'api.api',
    'entity.entity',
    'library.ester',
    'library.photo',
    'public.public',
    'screenwerk.screenwerk',
    'update.update',
    'main.config',
    'main.status',
    'user.auth',
    'user.user',
    'info.info',
]


class MainPage(myRequestHandler):
    """
    Redirects / to site's default path.

    """
    def get(self):
        self.redirect(self.app_settings['default_path'])


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
        settings_static = {
            'port':                 options.port,
            'debug':                True if str(options.debug).lower() == 'true' else False,
            'template_path':        path.join(path.dirname(__file__), '..', 'app'),
            'static_path':          path.join(path.dirname(__file__), '..', 'static'),
            'xsrf_coocies':         True,
            'login_url':            '/auth',
            'start_time':           time.time(),
            'request_count':        0,
            'request_time':         0,
            'slow_request_count':   0,
            'slow_request_time':    0,
            'databases':            {},
        }
        settings_yaml = yaml.safe_load(open('config.yaml', 'r'))

        # make DB connections
        for h, s in settings_yaml['hosts'].iteritems():
            settings_static['databases'][h] = torndb.Connection(
                host        = s['database']['host'],
                database    = s['database']['database'],
                user        = s['database']['user'],
                password    = s['database']['password'],
            )

        # load handlers
        handlers = [(r'/', MainPage)]
        for controller in app_controllers:
            c = __import__ (controller, globals(), locals(), ['*'], -1)
            handlers.extend(c.handlers)
            for h in c.handlers:
                settings_static.setdefault('paths', {}).setdefault('%s.py' % controller, []).append(h[0])
        handlers.append((r'(.*)', PageNotFound))

        # merge command line and static settings
        settings = dict(settings_static.items() + settings_yaml.items())

        # init application
        # logging.debug('App settings:\n%s' % yaml.safe_dump(settings, default_flow_style=False, allow_unicode=True))
        tornado.web.Application.__init__(self, handlers, **settings)


if __name__ == '__main__':
    tornado.locale.load_translations(path.join(path.dirname(__file__), '..', 'translation'))
    tornado.options.parse_command_line()
    tornado.httpserver.HTTPServer(myApplication(), xheaders=True).listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
