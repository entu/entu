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


from helper import *


# Command line options
define('debug', help='run on debug mode',     type=str, default='False')
define('port',  help='run on the given port', type=int, default=8000)


# List of controllers to load.
app_controllers = [
    'action.csv_import',
    'action.ester',
    'api',
    'auth',
    'entity',
    'public',
    'update',
    'user',
    'xxx',
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
        self.set_status(404)
        self.add_header('Content-Type', 'text/plain; charset=utf-8')
        self.write('Page not found!')


class ShowStatus(myRequestHandler):
    @web.removeslash
    def get(self, url):
        self.add_header('Content-Type', 'text/plain; charset=utf-8')
        status = {
            'Entu': {
                'debug':    self.settings['debug'],
                'port':     self.settings['port'],
                'uptime':   str(datetime.timedelta(seconds=round(time.time() - self.settings['start_time'])))
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
            'port':             options.port,
            'debug':            True if str(options.debug).lower() == 'true' else False,
            'template_path':    path.join(path.dirname(__file__), '..', 'templates'),
            'static_path':      path.join(path.dirname(__file__), '..', 'static'),
            'xsrf_coocies':     True,
            'login_url':        '/auth',
            'start_time':       time.time(),
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
    tornado.locale.load_translations(path.join(path.dirname(__file__), '..', 'translations'))
    tornado.options.parse_command_line()
    tornado.httpserver.HTTPServer(myApplication(), xheaders=True).listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


    # server = tornado.httpserver.HTTPServer(myApplication(), xheaders=True)
    # server.listen(options.port)

    # io_loop = tornado.ioloop.IOLoop.instance()
    # io_loop.set_blocking_signal_threshold(1, io_loop.log_stack)
    # io_loop.start()


