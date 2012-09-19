from tornado import web
from helper import *


class ShowStatus(myRequestHandler):
    @web.removeslash
    def get(self):
        self.require_setting('app_title', 'this application')
        self.require_setting('app_organisation', 'this application')

        self.write('%s - %s'  % (self.settings['app_title'], self.settings['app_organisation']))


handlers = [
    ('/status', ShowStatus),
]
