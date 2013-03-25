from os import path

import tornado.ioloop
import tornado.locale
import tornado.web
import tornado.httpserver
import tornado.database
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
        self.redirect(self.app_settings['default_path'])


class PageNotFound(myRequestHandler):
    """
    """
    def get(self, page=None):
        self.missing()


class ShowStatus(myRequestHandler):
    @web.removeslash
    def get(self, url):
        self.add_header('Content-Type', 'text/plain; charset=utf-8')

        status = {}
        if url == '/database':
            for s in self.settings['hosts'].values():
                db_connection = database.Connection(
                    host        = s['database']['host'],
                    database    = s['database']['database'],
                    user        = s['database']['user'],
                    password    = s['database']['password'],
                )
                size = db_connection.get('SELECT SUM(table_rows) AS table_rows,  SUM(data_length) AS data_length, SUM(index_length) AS index_length FROM information_schema.TABLES;')
                status.setdefault('Entu databases', {})[s['database']['database']] = {
                    'data': GetHumanReadableBytes(size.data_length, 2),
                    'index': GetHumanReadableBytes(size.index_length, 2),
                    'total': GetHumanReadableBytes(size.data_length+size.index_length, 2),
                }
        else:
            status = {
                'Entu service %s' % self.settings['port']: {
                    'uptime': str(datetime.timedelta(seconds=round(time.time() - self.settings['start_time']))),
                    'requests': {
                        'time': '%0.3fms' % round(float(self.settings['request_time'])/float(self.settings['request_count'])*1000, 3) if self.settings['request_count'] else 0,
                        'count': self.settings['request_count'],
                    },
                    'slow_requests': {
                        'time': '%0.3fs' % round(float(self.settings['slow_request_time'])/float(self.settings['slow_request_count']), 3) if self.settings['slow_request_count'] else 0,
                        'count': self.settings['slow_request_count'],
                    }
                }
            }

        self.write(yaml.safe_dump(status, default_flow_style=False, allow_unicode=True))


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
        }
        settings_yaml = yaml.safe_load(open('config.yaml', 'r'))

        # load handlers
        handlers = [(r'/', MainPage)]
        for controller in app_controllers:
            c = __import__ (controller, globals(), locals(), ['*'], -1)
            handlers.extend(c.handlers)
            for h in c.handlers:
                settings_static.setdefault('paths', {}).setdefault('%s.py' % controller, []).append(h[0])
        handlers.append((r'/status(.*)', ShowStatus))
        handlers.append((r'(.*)', PageNotFound))

        # merge command line and static settings
        settings = dict(settings_static.items() + settings_yaml.items())

        # init application
        # logging.debug('App settings:\n%s' % yaml.safe_dump(settings, default_flow_style=False, allow_unicode=True))
        tornado.web.Application.__init__(self, handlers, **settings)


if __name__ == '__main__':
    tornado.options.enable_pretty_logging()
    tornado.locale.load_translations(path.join(path.dirname(__file__), '..', 'translation'))
    tornado.options.parse_command_line()
    tornado.httpserver.HTTPServer(myApplication(), xheaders=True).listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


    # server = tornado.httpserver.HTTPServer(myApplication(), xheaders=True)
    # server.listen(options.port)

    # io_loop = tornado.ioloop.IOLoop.instance()
    # io_loop.set_blocking_signal_threshold(1, io_loop.log_stack)
    # io_loop.start()


