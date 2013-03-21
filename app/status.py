from tornado import web

from helper import *
from db import *


class ShowStatus(myRequestHandler):
    @web.removeslash
    def get(self):
        count = self.db.get('SELECT COUNT(DISTINCT entity_id) AS entities, COUNT(*) AS properties FROM property WHERE is_deleted = 0;')

        self.add_header('Content-Type', 'text/plain; charset=utf-8')
        self.write('%s\n'  % self.app_settings['app_title'])
        self.write('Organisation: %s\n'  % self.app_settings['app_organisation'])
        self.write('Entities:     %s\n'  % count.entities)
        self.write('Properties:   %s\n'  % count.properties)


handlers = [
    ('/status', ShowStatus),
]
