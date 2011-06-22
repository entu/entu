from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from django.utils import simplejson
import datetime
import urllib

from bo import *
from database.general import *
from database.person import *


class ShowDocumentsList(boRequestHandler):
    def get(self):
        docs = db.Query(Document).filter('owners', Person().current).fetch(1000)

        self.view('documents', 'documents/documents_list.html', {
            'documents': docs,
        })


class UploadDocument(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):

        upload_files = self.get_uploads('file')

        if upload_files:
            key = self.request.get('key').strip()
            entities = self.request.get('entities').strip()
            types = self.request.get('types').strip()
            title = self.request.get('title').strip()
            visibility = self.request.get('visibility').strip()

            blob_info = upload_files[0]

            doc = None
            if key:
                doc = Document().get(key)

            if not doc:
                p =  Person().current_s(self)
                doc = Document()
                if title:
                    d = Dictionary()
                    d.name = 'document_title'
                    setattr(d, UserPreferences().current.language, title)
                    doc.title = d.add()
                doc.types = StrToList(types)
                doc.entities = StrToKeyList(entities)
                doc.uploader = p
                doc.owners = [p.key()]
                if visibility in ['private', 'domain', 'public']:
                    doc.visibility = visibility

            doc.file = blob_info.key()
            doc.put()

            respond = {
                'key': str(doc.key()),
                'url': doc.url,
                'filename': doc.file.filename,
                'title': title,
                'visibility': visibility,
            }

            self.response.out.write(simplejson.dumps(respond))


class UpdateDocumentData(boRequestHandler):
    def post(self):
        key = self.request.get('key').strip()
        field = self.request.get('field').strip()
        value = self.request.get('value').strip()

        doc = Document().get(key)
        if doc:
            if field == 'name':
                d = Dictionary()
                setattr(d, UserPreferences().current.language, value)
                doc.title = d.add()
                doc.put()


class GetDocument(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, url):
        urls = url.split('/')

        key = urls[0]

        if len(urls) > 1:
            size = '=s' + urls[1]
        else:
            size = ''

        if len(urls) > 2:
            crop = '-c'
        else:
            crop = ''

        #try:
        image_types = ['image/bmp', 'image/jpeg', 'image/pjpeg', 'image/png', 'image/gif', 'image/tiff', 'image/x-icon']
        doc = Document().get(key)
        if doc.file.content_type in image_types:
            self.redirect(images.get_serving_url(doc.file.key()) + size + crop)
        else:
            self.send_blob(doc.file, save_as=doc.file.filename)
        #except:
        #    self.error(404)


class GetSize(boRequestHandler):
    def get(self):
        total = 0
        for b in blobstore.BlobInfo.all():
            total = total + b.size
            #self.echo(b.filename + ' - ' + str(b.size) + '\n')
        self.echo(str(total/1024/1024) + 'MB')
        self.echo(str(Document().all().count(limit=10000000)) + ' documents')


class Update1(boRequestHandler):
    def get(self):
        for doc in db.Query(Document).fetch(1000):
            doc.visibility = 'domain'
            doc.put()



def main():
    Route([
            ('/document', ShowDocumentsList),
            ('/document/upload', UploadDocument),
            ('/document/update', UpdateDocumentData),
            ('/document/update1', Update1),
            ('/document/size', GetSize),
            (r'/document/(.*)', GetDocument),
        ])


if __name__ == '__main__':
    main()