import torndb

import yaml
import logging
from operator import itemgetter

from main.helper import *
from main.db import *

class ShowDbSizes(myRequestHandler):
    @web.removeslash
    def get(self):
        self.add_header('Content-Type', 'text/plain; charset=utf-8')

        status = {}
        for s in self.settings['hosts'].values():
            db_connection = torndb.Connection(
                host        = s['database']['host'],
                database    = s['database']['database'],
                user        = s['database']['user'],
                password    = s['database']['password'],
            )
            size = db_connection.get('SELECT SUM(table_rows) AS table_rows,  SUM(data_length) AS data_length, SUM(index_length) AS index_length FROM information_schema.TABLES;')
            status[s['database']['database']] = {
                'total': GetHumanReadableBytes(size.data_length+size.index_length, 2),
                'data': GetHumanReadableBytes(size.data_length, 2),
                'index': GetHumanReadableBytes(size.index_length, 2),
            }

        # self.write(yaml.safe_dump(sorted(status, key=itemgetter('total'), reverse=True), default_flow_style=False, allow_unicode=True))
        self.write(yaml.safe_dump(status, default_flow_style=False, allow_unicode=True))


class ShowStatus(myRequestHandler):
    @web.removeslash
    def get(self, url):
        self.add_header('Content-Type', 'text/plain; charset=utf-8')

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


handlers = [
    (r'/status/size', ShowDbSizes),
    (r'/status(.*)', ShowStatus),
]
