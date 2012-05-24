from tornado.web import RequestHandler
from tornado.options import options
from tornado import locale

from operator import itemgetter
import urllib
import magic

from helper import *
from db import *


class PublicHandler(myRequestHandler):
    def get(self):
        self.render('public/start.html',
            page_title = self.locale.translate('search_results'),
            search = ''
        )


class PublicSearchHandler(myRequestHandler):
    def get(self, search=None):
        if not search:
            self.redirect('/public')

        locale = self.get_user_locale()
        items = []
        if len(search) > 1:
            for item in myDb().getBubbleList(search=search, only_public=True, bubble_definition=[1, 7, 8, 38]):
                name = ', '.join([x['value'] for x in item.setdefault('properties', {}).setdefault('title', {}).setdefault('values', {}).values()])
                number = ', '.join([x['value'] for x in item.setdefault('properties', {}).setdefault('registry_number', {}).setdefault('values', {}).values()])
                items.append({
                    'url': '/public/%s/%s' % (item.setdefault('id', ''), toURL(name)),
                    'number': number,
                    'name': name,
                    'date': item.setdefault('created', '').strftime('%d.%m.%Y'),
                    'file': len(item.setdefault('properties', {}).setdefault('public_files', {}).setdefault('values', {}).values()),
                })

        if len(search) < 2:
            itemcount =locale.translate('search_term_to_short') % search
        elif len(items) == 0:
            itemcount =locale.translate('search_noresult')
        elif len(items) == 1:
            itemcount =locale.translate('search_result_count1')
        else:
            itemcount =locale.translate('search_result_count2') % len(items)

        self.render('public/list.html',
            page_title = self.locale.translate('search_results'),
            items = sorted(items, key=itemgetter('name')) ,
            itemcount = itemcount,
            search = urllib.unquote_plus(search)
        )


    def post(self):
        search_get = self.get_argument('search', None)
        if not search_get:
            self.redirect('/public')
        self.redirect('/public/search/%s' % urllib.quote_plus(search_get))


class PublicItemHandler(myRequestHandler):
    def get(self, id=None, url=None):
        item = myDb().getBubbleList(id=id, only_public=True, limit=1)
        if not item:
            self.redirect('/public')

        item = item[0]
        item_name = ', '.join([x['value'] for x in item.setdefault('properties', {}).setdefault('title', {}).setdefault('values', {}).values()])

        props = []
        for p in item.setdefault('properties', {}).values():
            if p.setdefault('dataproperty', '') == 'title':
                continue
            if p.setdefault('datatype', '') == 'blobstore':
                value = '<br />'.join(['<a href="/public/file/%s/%s" title="%s">%s</a>' % (x['file_id'], toURL(x['value']), x['filesize'], x['value']) for x in p.setdefault('values', {}).values() if x['value']])
            else:
                value = '<br />'.join([x['value'] for x in p.setdefault('values', {}).values() if x['value']])

            props.append({
                'ordinal' : p.setdefault('ordinal', 0),
                'label' : p.setdefault('label', ''),
                'value': value
            })

        self.render('public/item.html',
            page_title = item_name,
            item_name = item_name,
            properties = sorted(props, key=itemgetter('ordinal')),
            search = ''
        )


class PublicFileHandler(myRequestHandler):
    def get(self, id=None, url=None):
        file = myDb().getFile(id, True)
        if not file:
            return self.missing()

        ms = magic.open(magic.MAGIC_MIME)
        ms.load()
        mime = ms.buffer(file.file)
        ms.close()

        self.add_header('Content-Type', mime)
        self.add_header('Content-Disposition', 'attachment; filename="%s"' % file.filename)
        self.write(file.file)


handlers = [
    (r'/public', PublicHandler),
    (r'/public/search', PublicSearchHandler),
    (r'/public/search/(.*)', PublicSearchHandler),
    (r'/public/file/([0-9]+)', PublicFileHandler),
    (r'/public/file/([0-9]+)/(.*)', PublicFileHandler),
    (r'/public/([0-9]+)', PublicItemHandler),
    (r'/public/([0-9]+)/(.*)', PublicItemHandler),
]
