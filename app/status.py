from tornado import web
from helper import *


class ShowStatus(myRequestHandler):
    @web.removeslash
    def get(self):
        self.require_setting('app_title', 'this application')
        self.require_setting('app_organisation', 'this application')

        db_connection = db.connection()
        count = db_connection.get('SELECT COUNT(DISTINCT entity_id) AS entities, COUNT(*) AS properties FROM property;')

        self.add_header('Content-Type', 'text/plain; charset=utf-8')
        self.write('%s\n'  % self.settings['app_title'])
        self.write('Organisation: %s\n'  % self.settings['app_organisation'])
        self.write('Entities:     %s\n'  % count.entities)
        self.write('Properties:   %s\n'  % count.properties)


handlers = [
    ('/status', ShowStatus),
]
