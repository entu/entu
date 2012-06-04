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
            #entities = db.Entity(user_locale=self.get_user_locale()).get(search=search, entity_definition_id=[1, 7, 8, 38])
            entities = db.Entity(user_locale=self.get_user_locale()).get(search=search)
            if entities:
                for item in entities:
                    items.append({
                        'url': '/public/entity-%s/%s' % (item.get('id', ''), toURL(item.get('displayname', ''))),
                        'name': item.get('displayname', ''),
                        'date': item.get('created', '').strftime('%d.%m.%Y'),
                        'file': item.get('file_count', 0),
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
            entities = sorted(items, key=itemgetter('name')) ,
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

        self.render('public/item.html',
            page_title = item['displayname'],
            entity = item,
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
