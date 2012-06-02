from tornado import web
from tornado import httpclient

import logging

from helper import *
from db import *


class GAEsql(myRequestHandler):
    def post(self):
        self.require_setting('app_title', 'GAE import')

        secret = self.settings['gae_secret']
        sql = self.get_argument('sql', None)

        logging.info('DESCRIPTION: %s' % self.get_argument('description', ''))

        if self.get_argument('secret', None) != secret or not sql:
            return self.forbidden()

        db.connection().execute(sql.replace('%%', '%%%%'))

        self.write('OK')


class GAEFiles(myRequestHandler):
    @web.asynchronous
    def get(self):
        self.add_header('Content-Type', 'text/plain; charset=utf-8')
        for f in db.connection().query('SELECT gae_key FROM file WHERE file IS NULL AND gae_key NOT LIKE \'amphora_%%\' ORDER BY gae_key;'):
            url = 'https://dev-m.bubbledu.appspot.com/export/file/%s' % f.gae_key
            httpclient.AsyncHTTPClient().fetch(url, callback=self._got_file)
        self.write('Done!')
        self.flush()

    def _got_file(self, response):
        if not response.body:
            return

        gae_key = response.request.url.replace('https://dev-m.bubbledu.appspot.com/export/file/', '').strip()
        db.connection().execute('UPDATE file SET filesize = %s, file = %s WHERE gae_key = %s;', len(response.body), response.body, gae_key)
        self.write('%s\n' % len(response.body))
        self.flush()


class AmphoraFiles(myRequestHandler):
    @web.asynchronous
    def get(self):
        pass


handlers = [
    (r'/import/gae', GAEsql),
    (r'/import/gae_files', GAEFiles),
    (r'/import/amphora_files', GAEFiles),
]
