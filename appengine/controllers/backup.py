from __future__ import with_statement
from google.appengine.api import files

from bo import *
from database.feedback import *
from datetime import datetime


class GoogleCloudStorage(boRequestHandler):
    def get(self):
        taskqueue.Task(url='/backup/gcs').add()


    def post(self):
        limit = 500
        step = int(self.request.get('step', 1))
        offset = int(self.request.get('offset', 0))

        bc = 0
        xmls = ''
        for b in db.Query(Bubble).order('__key__').fetch(limit=limit, offset=offset):
            bc += 1
            xmls += b.to_xml()

        filename = '/gs/bubbledu/%s/Bubble_%05d.gz' % (datetime.now().strftime('%Y%m%d'), step)
        writable_file_name = files.gs.create(filename, content_encoding='gzip')
        with files.open(writable_file_name, 'a') as f:
            f.write(xmls.encode('utf-8'))
        files.finalize(writable_file_name)

        logging.debug('#%s - %s' % (step, bc))

        # if bc == limit:
        #     taskqueue.Task(url='/backup/gcs', params={'offset': (offset + bc), 'step': (step + 1)}).add()

        self.echo('done')


def main():
    Route([
            ('/backup/gcs', GoogleCloudStorage),
        ])


if __name__ == '__main__':
    main()
