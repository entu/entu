from tornado import web
from tornado import httpclient

import logging

from helper import *
from db import *


class GAEFiles(myRequestHandler):
    @web.asynchronous
    def get(self):
        db = myDb().db
        for f in db.query('SELECT id, gae_key FROM file WHERE file IS NULL ORDER BY filesize DESC;'):
            url = 'https://dev-m.bubbledu.appspot.com/update/export/file/%s' % f.gae_key
            httpclient.AsyncHTTPClient().fetch(url, callback=self._got_file)
        db.close()
        self.write('Done!')
        self.flush()

    def _got_file(self, response):
        if not response.body:
            return

        db = myDb().db
        gae_key = response.request.url.replace('https://dev-m.bubbledu.appspot.com/update/export/file/', '').strip()
        db.execute('UPDATE file SET filesize = %s, file = %s WHERE gae_key = %s;', len(response.body), response.body, gae_key)
        db.close()
        self.write(str(len(response.body)))
        self.flush()


handlers = [
    (r'/import/gae_files', GAEFiles),
]
