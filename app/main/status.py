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


class ShowFileSizes(myRequestHandler):
    @web.removeslash
    def get(self):
        series_data = {}
        for s in self.settings['hosts'].values():
            db_connection = torndb.Connection(
                host        = s['database']['host'],
                database    = s['database']['database'],
                user        = s['database']['user'],
                password    = s['database']['password'],
            )
            files = db_connection.get("""
                SELECT
                    SUM(filesize) AS filesize,
                    DATE_FORMAT(created, '%Y-%m-%d') AS date
                FROM file
                GROUP BY
                    DATE_FORMAT(created, "%Y-%m-%d")
                ORDER BY date DESC
                LIMIT %s
                ;""", 7)

            series_data.setDefault(s['database']['database'], {})['name'] = s['database']['database']
            series_data.setDefault(s['database']['database'], {}).setDefault('data', []).push([files.date, files.filesize])

        self.json({
            'x_axis': {
                'type': 'datetime'
            },
            'series': series_data.values()
        })


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
    (r'/status/filesize', ShowFileSizes),
    (r'/status(.*)', ShowStatus),
]
