from tornado.web import RequestHandler
from tornado.options import options
from tornado import locale

from operator import itemgetter
import urllib

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
            for item in myDb().getBubbleList(search=search, only_public=True, bubble_definition=[55, 61, 62, 92]):
                name = ', '.join([x['value'] for x in item.setdefault('properties', {}).setdefault('title', {}).setdefault('values', {}).values()])
                number = ', '.join([x['value'] for x in item.setdefault('properties', {}).setdefault('registry_number', {}).setdefault('values', {}).values()])
                items.append({
                    'url': '/public/%s/%s' % (item.setdefault('id', ''), toURL(name)),
                    'number': number,
                    'name': name,
                    'date': item.setdefault('created', '').strftime('%d.%m.%Y'),
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
            props.append({
                'ordinal' : p.setdefault('ordinal', 0),
                'label' : p.setdefault('label', ''),
                'value': ', '.join([x['value'] for x in p.setdefault('values', {}).values()]),
            })

        self.render('public/item.html',
            page_title = item_name,
            item_name = item_name,
            properties = sorted(props, key=itemgetter('ordinal')),
            search = ''
        )


handlers = [
    (r'/public', PublicHandler),
    (r'/public/search', PublicSearchHandler),
    (r'/public/search/(.*)', PublicSearchHandler),
    (r'/public/([0-9]+)', PublicItemHandler),
    (r'/public/([0-9]+)/(.*)', PublicItemHandler),
]
