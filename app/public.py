from tornado.options import options
from tornado import web

from operator import itemgetter
import urllib
import magic

import db
from helper import *


class PublicHandler(myRequestHandler):
    """
    Show public startpage.

    """
    @web.removeslash
    def get(self, path=None):
        path = path.strip('/').strip('-')
        db_connection = db.connection()
        if not path:
            path = db_connection.get('SELECT public_path FROM entity_definition WHERE public_path IS NOT NULL ORDER BY public_path LIMIT 1;')
            if path:
                return self.redirect('/public-%s' % path.public_path)
            else:
                return self.missing()


        self.render('public/start.html',
            paths = get_paths(self.get_user_locale()),
            path = path,
            search = '',
            entity_definitions = get_definitions(self.get_user_locale(), path)
        )


class PublicSearchHandler(myRequestHandler):
    """
    Show public search results.

    """
    def get(self, path=None, search=None):
        if not path:
            self.redirect('/public')

        search = search.strip('/').strip('-')
        if not search:
            self.redirect('/public-%s' % path)

        locale = self.get_user_locale()
        items = []
        if len(search) > 1:
            db_connection = db.connection()
            entity_definitions = [x.id for x in db_connection.query('SELECT id FROM entity_definition WHERE public_path = %s;', path)]

            entities = db.Entity(user_locale=self.get_user_locale()).get(search=search, entity_definition_id=entity_definitions, only_public=True)
            if entities:
                for item in entities:
                    items.append({
                        'url': '/public-%s/entity-%s/%s' % (path, item.get('id', ''), toURL(item.get('displayname', ''))),
                        'name': item.get('displayname', ''),
                        'date': item.get('created'),
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
            entities = sorted(items, key=itemgetter('name')) ,
            itemcount = itemcount,
            paths = get_paths(self.get_user_locale()),
            path = path,
            search = urllib.unquote_plus(search),
        )


    def post(self, path=None, search=None   ):
        search_get = self.get_argument('search', None)
        if not path or not search_get:
            self.redirect('/public')
        self.redirect('/public-%s/search/%s' % (path, urllib.quote_plus(search_get.encode('utf-8'))))


class PublicAdvancedSearchHandler(myRequestHandler):
    """
    Show public advanced search results.

    """
    def get(self, path=None, search=None):
        if not path:
            self.redirect('/public')

        if not self.get_argument('ed', None):
            self.redirect('/public-%s' % path)

        entity_definition_id = int(self.get_argument('ed'))

        entity = db.Entity(user_locale=self.get_user_locale())
        entity_definition = entity.get(entity_id=0, entity_definition_id=entity_definition_id, full_definition=True, limit=1, only_public=True)

        db_connection = db.connection()
        entity_ids = None

        for p in entity_definition.get('properties', {}).values():
            if not p['public'] or p['datatype'] not in ['string', 'text', 'datetime', 'date', 'integer', 'decimal', 'boolean', 'counter_value']:
                continue

            sql = ''

            if p['datatype'] in ['string', 'counter_value']:
                if self.get_argument('t%s' % p['id'], None):
                    sql += ' AND value_string LIKE \'%%%%%s%%%%\'' % self.get_argument('t%s' % p['id']).replace('\'', '\\\'')

            if p['datatype'] in ['integer', 'decimal']:
                if self.get_argument('t%s' % p['id'], None):
                    sql += ' AND value_decimal = %s' % self.get_argument('t%s' % p['id']).replace('\'', '\\\'')

            elif p['datatype'] in ['datetime', 'date']:
                if self.get_argument('s%s' % p['id'], None):
                    sql += ' AND value_datetime >= \'%s\'' % self.get_argument('s%s' % p['id']).replace('\'', '\\\'')
                if self.get_argument('e%s' % p['id'], None):
                    sql += ' AND value_datetime <= \'%s\'' % self.get_argument('e%s' % p['id']).replace('\'', '\\\'')

            if sql:
                sql = 'SELECT DISTINCT entity.id FROM property, entity WHERE entity.id = property.entity_id AND entity.entity_definition_id = %s AND property.property_definition_id = %s AND entity.public = 1 %s' % (entity_definition_id, p['id'], sql)
                ids = [x.id for x in db_connection.query(sql)]
                if entity_ids == None:
                    entity_ids = ids
                entity_ids = ListMatch(entity_ids, ids)

        locale = self.get_user_locale()
        items = []
        if entity_ids:
            entity_definitions = [x.id for x in db_connection.query('SELECT id FROM entity_definition WHERE public_path = %s;', path)]

            entities = db.Entity(user_locale=self.get_user_locale()).get(entity_id=entity_ids, entity_definition_id=entity_definitions, only_public=True)
            if entities:
                for item in entities:
                    items.append({
                        'url': '/public-%s/entity-%s/%s' % (path, item.get('id', ''), toURL(item.get('displayname', ''))),
                        'name': item.get('displayname', ''),
                        'date': item.get('created'),
                        'file': item.get('file_count', 0),
                    })

        if len(items) == 0:
            itemcount =locale.translate('search_noresult')
        elif len(items) == 1:
            itemcount =locale.translate('search_result_count1')
        else:
            itemcount =locale.translate('search_result_count2') % len(items)

        self.render('public/list.html',
            entities = sorted(items, key=itemgetter('name')) ,
            itemcount = itemcount,
            paths = get_paths(self.get_user_locale()),
            path = path,
            search = '',
        )


class PublicEntityHandler(myRequestHandler):
    """
    Show public entity.

    """
    def get(self, path=None, entity_id=None, url=None):
        try:
            entity_id = int(entity_id.split('/')[0])
        except:
            return self.missing()

        item = db.Entity(user_locale=self.get_user_locale()).get(entity_id=entity_id, limit=1, only_public=True)
        if not item:
            return self.missing()

        self.render('public/item.html',
            page_title = item['displayname'],
            entity = item,
            paths = get_paths(self.get_user_locale()),
            path = path,
            search = '',
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


def get_paths(user_locale):
    db_connection = db.connection()
    return db_connection.query('SELECT DISTINCT public_path AS path, %s_public AS label FROM entity_definition WHERE public_path IS NOT NULL ORDER BY public_path;' % user_locale.code)


def get_definitions(user_locale, path):
    db_connection = db.connection()
    entity_definitions = []
    entity = db.Entity(user_locale=user_locale)
    for entity_definition_id in [x.id for x in db_connection.query('SELECT id FROM entity_definition WHERE public_path = %s;', path)]:
        entity_definitions.append(entity.get(entity_id=0, entity_definition_id=entity_definition_id, full_definition=True, limit=1, only_public=True))
    return entity_definitions


handlers = [
    (r'/public-(.*)/search2', PublicAdvancedSearchHandler),
    (r'/public-(.*)/search(.*)', PublicSearchHandler),
    (r'/public-(.*)/entity-(.*)', PublicEntityHandler),
    (r'/public/file-(.*)', PublicFileHandler),
    (r'/public(.*)', PublicHandler),
]
