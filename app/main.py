from os import path

import tornado.ioloop
import tornado.locale
import tornado.web
import tornado.httpserver
import tornado.options

import os
import yaml
import logging
import string
import datetime, time


from main.helper import *
from main.db import *


# global variables (and list of all used environment variables)
APP_VERSION        = os.getenv('VERSION', tornado.version)
APP_DEBUG          = str(os.getenv('DEBUG', 'false')).lower() == 'true'
APP_PORT           = os.getenv('PORT', 80)
APP_COOKIE_DOMAIN  = os.getenv('COOKIE_DOMAIN', '.entu.ee')
APP_AUTH_URL       = os.getenv('AUTH_URL', 'https://auth.entu.ee')
APP_AUTH_ID        = os.getenv('AUTH_ID')
APP_AUTH_SECRET    = os.getenv('AUTH_SECRET')
APP_UPLOADS_PATH   = os.getenv('UPLOADS_PATH')
APP_MONGODB        = os.getenv('MONGODB', 'mongodb://entu_mongodb:27017/')
APP_MYSQL_HOST     = os.getenv('MYSQL_HOST', 'localhost')
APP_MYSQL_PORT     = os.getenv('MYSQL_PORT', 3306)
APP_MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')
APP_MYSQL_USER     = os.getenv('MYSQL_USER')
APP_MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
APP_MYSQL_SSL_CA   = os.getenv('MYSQL_SSL_CA')
APP_CUSTOMERGROUP  = os.getenv('CUSTOMERGROUP')
APP_FILES_PATH     = os.getenv('FILES_PATH')


# List of controllers to load.
app_controllers = [
    'api.api2',
    'entity.csv_import',
    'entity.entity',
    'library.ester',
    'library.photo',
    'main.config',
    'main.status',
    'public.public',
    'user.auth',
]


class MainPage(myRequestHandler):
    """
    Redirects / to site's default path.

    """
    def get(self):
        if self.current_user and '{CURRENT_USER}' in self.app_settings('path'):
            self.redirect(self.app_settings('path').replace('{CURRENT_USER}', '%s' % self.current_user.get('id')))
        elif self.app_settings('path'):
            self.redirect(self.app_settings('path'))
        else:
            logging.error('MainPage redirect failed for ' + self.request.method + ' ' + self.request.host + self.request.uri)


class PageNotFound(myRequestHandler):
    """
    """
    def get(self, page=None):
        logging.error('404 - ' + self.request.method + ' ' + self.request.host + self.request.uri)

        try:
            self.missing()
        except Exception:
            pass


class myApplication(tornado.web.Application):
    """
    Main Application handler. Imports controllers, settings, translations.

    """
    def __init__(self):
        # load settings
        settings = {
            'port':                 APP_PORT,
            'debug':                APP_DEBUG,
            'template_path':        path.join(path.dirname(__file__), '..', 'app'),
            'static_path':          path.join(path.dirname(__file__), '..', 'static'),
            'xsrf_coocies':         True,
            'login_url':            '/auth',
            'auth_url':             APP_AUTH_URL,
            'auth_id':              APP_AUTH_ID,
            'auth_secret':          APP_AUTH_SECRET,
            'cookie_domain':        APP_COOKIE_DOMAIN,
            'start_time':           time.time(),
            'request_count':        0,
            'request_time':         0,
            'slow_request_count':   0,
            'slow_request_time':    0,
            'slow_request_ms':      1000,
            'uploads_path':         APP_UPLOADS_PATH,
            'mongodb':              APP_MONGODB,
            'database-host':        APP_MYSQL_HOST,
            'database-port':        APP_MYSQL_PORT,
            'database-database':    APP_MYSQL_DATABASE,
            'database-user':        APP_MYSQL_USER,
            'database-password':    APP_MYSQL_PASSWORD,
            'database-ssl-ca':      APP_MYSQL_SSL_CA,
            'files-path':           APP_FILES_PATH,
            'customergroup':        APP_CUSTOMERGROUP,
            'mongodbs':             {},
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

        logging.warning('Tornado %s started to listen %s' % (APP_VERSION, APP_PORT))

        # init application
        tornado.web.Application.__init__(self, handlers, **settings)


if __name__ == '__main__':
    tornado.options.parse_command_line()
    tornado.locale.load_translations(path.join(path.dirname(__file__), 'main', 'translation'))

    application = myApplication()

    server = tornado.httpserver.HTTPServer(application, xheaders=True, max_body_size=1024*1024*1024*5)

    if APP_DEBUG:
        server.listen(APP_PORT)
    else:
        server.bind(APP_PORT)
        server.start(0)

    tornado.ioloop.IOLoop.current().start()
