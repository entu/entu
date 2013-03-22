from tornado import web

from helper import *


class ShowStatus(myRequestHandler):
    @web.removeslash
    def get(self, url):
        self.add_header('Content-Type', 'text/plain; charset=utf-8')
        self.write('Entu is up!')


handlers = [
    ('/status(.*)', ShowStatus),
]
