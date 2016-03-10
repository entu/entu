import torndb

import logging

from main.helper import *


class ShowDbSizes(myRequestHandler):
    @web.removeslash
    def get(self):
        result = {}
        for s in self._app_settings.values():
            db_connection = torndb.Connection(
                host        = s['database']['host'],
                database    = s['database']['database'],
                user        = s['database']['user'],
                password    = s['database']['password'],
            )
            size = db_connection.get('SELECT SUM(table_rows) AS table_rows,  SUM(data_length) AS data_length, SUM(index_length) AS index_length FROM information_schema.TABLES;')
            result[s['database']['database']] = {
                'total': size.data_length+size.index_length,
                'data': size.data_length,
                'index': size.index_length,
            }

        self.json(result)


class ShowFileSizes(myRequestHandler):
    @web.removeslash
    def get(self):
        days = self.get_argument('days', default=7, strip=True),

        series_data = {}
        for s in self._app_settings.values():
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
                ;""", days)

            series_data.setDefault(s['database']['database'], {})['name'] = s['database']['database']
            series_data.setDefault(s['database']['database'], {}).setDefault('data', []).push([files.date, files.filesize])

        self.json({
            'x_axis': {
                'type': 'datetime'
            },
            'series': series_data.values()
        })


handlers = [
    (r'/status/dbsize', ShowDbSizes),
    (r'/status/filesize', ShowFileSizes),
]
