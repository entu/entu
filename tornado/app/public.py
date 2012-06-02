from tornado.web import RequestHandler
from tornado.options import options
from tornado import locale

from operator import itemgetter
import urllib
import magic

import db
from helper import *


class PublicHandler(myRequestHandler):
    """
    Show public startpage.

    """
    def get(self):
        self.render('public/start.html',
            page_title = self.locale.translate('search_results'),
            search = ''
        )


class PublicSearchHandler(myRequestHandler):
    """
    Show public search results.

    """
    def get(self, search=None):
        if not search:
            self.redirect('/public')

        locale = self.get_user_locale()
        items = []
        if len(search) > 1:
            #entities = db.Entity(user_locale=self.get_user_locale()).get(search=search, entity_definition=[1, 7, 8, 38])
            entities = db.Entity(user_locale=self.get_user_locale()).get(search=search)
            if entities:
                for item in entities:
                    name = ', '.join([x['value'] for x in item.get('properties', {}).get('title', {}).get('values', {}).values()])
                    number = ', '.join([x['value'] for x in item.get('properties', {}).get('registry_number', {}).get('values', {}).values()])
                    items.append({
                        'url': '/public/entity-%s/%s' % (item.get('id', ''), toURL(name)),
                        'number': number,
                        'name': name,
                        'date': item.get('created', '').strftime('%d.%m.%Y'),
                        'file': len(item.get('properties', {}).get('public_files', {}).get('values', {}).values()),
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
        self.redirect('/public/search/%s' % urllib.quote_plus(search_get.encode('utf-8')))


class PublicEntityHandler(myRequestHandler):
    """
    Show public entity.

    """
    def get(self, entity_id=None, url=None):
        try:
            entity_id = int(entity_id.split('/')[0])
        except:
            return self.missing()

        item = db.Entity(user_locale=self.get_user_locale()).get(entity_id=entity_id, limit=1)
        if not item:
            return self.missing()

        item = item[0]
        item_name = ', '.join([x['value'] for x in item.get('properties', {}).get('title', {}).get('values', {}).values()])

        props = []
        for p in item.get('properties', {}).values():
            if p.get('dataproperty', '') == 'title':
                continue
            if p.get('datatype', '') == 'file':
                value = '<br />'.join(['<a href="/public/file-%s/%s" title="%s">%s</a>' % (x['file_id'], toURL(x['value']), x['filesize'], x['value']) for x in p.get('values', {}).values() if x['value']])
            else:
                value = '<br />'.join([x['value'] for x in p.get('values', {}).values() if x['value']])

            props.append({
                'ordinal' : p.get('ordinal', 0),
                'label' : p.get('label', ''),
                'value': value
            })

        self.render('public/item.html',
            page_title = item_name,
            item_name = item_name,
            properties = sorted(props, key=itemgetter('ordinal')),
            search = ''
        )


class PublicFileHandler(myRequestHandler):
    """
    Download public file.

    """
    def get(self, file_id=None, url=None):
        try:
            file_id = int(file_id.split('/')[0])
        except:
            return self.missing()

        file = db.Entity(user_locale=self.get_user_locale()).get_file(file_id)
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
    (r'/public/file-(.*)', PublicFileHandler),
    (r'/public/entity-(.*)', PublicEntityHandler),
]
