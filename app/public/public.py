from tornado import web

from operator import itemgetter
import urllib
import mimetypes

from main.helper import *
from main.db import *
from main.db2 import *


class PublicHandler(myRequestHandler, Entity):
    """
    Show public startpage.

    """
    @web.removeslash
    def get(self, path=None):
        path = path.strip('/').strip('-')
        if not path:
            path = self.db.get('SELECT public_path FROM entity_definition WHERE public_path IS NOT NULL ORDER BY public_path LIMIT 1;')
            if path:
                return self.redirect('/public-%s' % path.public_path)
            else:
                return self.missing()


        self.render('public/template/start.html',
            paths = self.get_public_paths(),
            path = path,
            search = ''
        )


class PublicSearchHandler(myRequestHandler, Entity2):
    """
    Show public search results.

    """
    def get(self, path=None, search=None):
        if not path:
            self.redirect('/public')

        search = urllib.unquote_plus(search.strip('/').strip('-'))
        if not search:
            self.redirect('/public-%s' % path)

        locale = self.get_user_locale()
        items = []
        if len(search) > 1:
            entity_definitions = [x.keyname for x in self.db.query('SELECT keyname FROM entity_definition WHERE public_path = %s;', path)]

            entities = self.get_entities_info(query=search, definition=entity_definitions)
            logging.warning(search)
            if entities:
                for item in entities.get('entities', []):
                    items.append({
                        'id': item.get('id', ''),
                        'url': '/public-%s/entity-%s/%s' % (path, item.get('id', ''), toURL(item.get('displayname', ''))),
                        'name': item.get('displayname', ''),
                        'info': item.get('displayinfo', ''),
                        'date': item.get('created'),
                        'picture': item.get('displaypicture', ''),
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

        self.render('public/template/list.html',
            entities = sorted(items, key=itemgetter('name')) ,
            itemcount = itemcount,
            paths = self.get_public_paths(),
            path = path,
            search = urllib.unquote_plus(search),
        )


    def post(self, path=None, search=None   ):
        search_get = self.get_argument('search', None)
        if not path or not search_get:
            self.redirect('/public')
        self.redirect('/public-%s/search/%s' % (path, urllib.quote_plus(search_get.encode('utf-8'))))


class PublicAdvancedSearchHandler(myRequestHandler, Entity):
    """
    Show public advanced search results.

    """
    def get(self, path=None, search=None):
        if not path:
            self.redirect('/public')

        if not self.get_argument('ed', None):
            self.redirect('/public-%s' % path)

        entity_definition_keyname = self.get_argument('ed')

        entity_definition = self.get_entities(entity_id=0, entity_definition_keyname=entity_definition_keyname, full_definition=True, limit=1, only_public=True)

        entity_ids = None

        for p in entity_definition.get('properties', {}).values():
            if not p['public'] or p['datatype'] not in ['string', 'text', 'datetime', 'date', 'integer', 'decimal', 'boolean', 'counter_value']:
                continue

            sql = ''

            if p['datatype'] in ['string', 'counter_value']:
                if self.get_argument('t%s' % p['keyname'], None):
                    sql += ' AND value_string LIKE \'%%%%%s%%%%\'' % self.get_argument('t%s' % p['keyname']).replace('\'', '\\\'')

            if p['datatype'] in ['integer', 'decimal']:
                if self.get_argument('t%s' % p['keyname'], None):
                    sql += ' AND value_decimal = %s' % self.get_argument('t%s' % p['keyname']).replace('\'', '\\\'')

            elif p['datatype'] in ['datetime', 'date']:
                if self.get_argument('s%s' % p['keyname'], None):
                    sql += ' AND value_datetime >= \'%s\'' % self.get_argument('s%s' % p['keyname']).replace('\'', '\\\'')
                if self.get_argument('e%s' % p['keyname'], None):
                    sql += ' AND value_datetime <= \'%s\'' % self.get_argument('e%s' % p['keyname']).replace('\'', '\\\'')

            if sql:
                sql = 'SELECT DISTINCT entity.id FROM property, entity WHERE entity.id = property.entity_id AND entity.entity_definition_keyname = \'%s\' AND property.property_definition_keyname = \'%s\' AND entity.sharing = \'public\' %s' % (entity_definition_keyname, p['keyname'], sql)
                logging.debug(sql)
                ids = [x.id for x in self.db.query(sql)]
                if entity_ids == None:
                    entity_ids = ids
                entity_ids = ListMatch(entity_ids, ids)

        locale = self.get_user_locale()
        items = []
        if entity_ids:
            entity_definitions = [x.keyname for x in self.db.query('SELECT keyname FROM entity_definition WHERE public_path = %s;', path)]

            entities = self.get_entities(entity_id=entity_ids, entity_definition_keyname=entity_definitions, only_public=True)
            if entities:
                for item in entities:
                    items.append({
                        'url': '/public-%s/entity-%s/%s' % (path, item.get('id', ''), toURL(item.get('displayname', ''))),
                        'name': item.get('displayname', ''),
                        'picture': item.get('displaypicture', ''),
                        'date': item.get('created'),
                        'file': item.get('file_count', 0),
                    })

        if len(items) == 0:
            itemcount =locale.translate('search_noresult')
        elif len(items) == 1:
            itemcount =locale.translate('search_result_count1')
        else:
            itemcount =locale.translate('search_result_count2') % len(items)

        self.render('public/template/list.html',
            entities = sorted(items, key=itemgetter('name')) ,
            itemcount = itemcount,
            paths = self.get_public_paths(),
            path = path,
            search = '',
        )


class PublicEntityHandler(myRequestHandler, Entity):
    """
    Show public entity.

    """
    def get(self, path=None, entity_id=None, url=None):
        try:
            entity_id = int(entity_id.split('/')[0])
        except:
            return self.missing()

        item = self.get_entities(entity_id=entity_id, limit=1, only_public=True)
        if not item:
            return self.missing()

        self.render('public/template/item.html',
            page_title = item['displayname'],
            entity = item,
            paths = self.get_public_paths(),
            path = path,
            search = '',
            sharing_key = None,
        )


class SharedEntityWithKeyHandler(myRequestHandler, Entity):
    """
    Show public entity.

    """
    def get(self, entity_id=None, sharing_key=None):
        if not entity_id:
            return self.missing()

        if not sharing_key:
            return self.missing()

        item = self.get_entities(entity_id=entity_id, limit=1, only_public=True, sharing_key=sharing_key)
        if not item:
            return self.missing()

        self.render('public/template/item.html',
            page_title = item['displayname'],
            entity = item,
            paths = {},
            path = '',
            search = '',
            sharing_key = sharing_key,
        )


# class PublicFileHandler(myRequestHandler, Entity):
#     """
#     Download public file.

#     """
#     def get(self, file_id=None, url=None):
#         try:
#             file_id = int(file_id.split('/')[0])
#         except:
#             return self.missing()

#         sharing_key = self.get_argument('key', default=None, strip=True)

#         files = self.get_file(file_id=file_id, sharing_key=sharing_key)
#         if not files:
#             return self.missing()

#         f = files[0]

#         mimetypes.init()
#         mime = mimetypes.types_map.get('.%s' % f.get('filename').lower().split('.')[-1], 'application/octet-stream')

#         self.add_header('Content-Type', mime)
#         self.add_header('Content-Disposition', 'inline; filename="%s"' % f.get('filename'))
#         self.write(f.get('file'))


def get_definitions(rh, path):
    entity_definitions = []
    for entity_definition_keyname in [x.keyname for x in rh.db.query('SELECT keyname FROM entity_definition WHERE public_path = %s;', path)]:
        entity_definitions.append(rh.get_entities(entity_id=0, entity_definition_keyname=entity_definition_keyname, full_definition=True, limit=1, only_public=True))
    return entity_definitions


handlers = [
    (r'/public-(.*)/search2', PublicAdvancedSearchHandler),
    (r'/public-(.*)/search(.*)', PublicSearchHandler),
    (r'/public-(.*)/entity-(.*)', PublicEntityHandler),
    # (r'/public/file-(.*)', PublicFileHandler),
    (r'/public(.*)', PublicHandler),
    (r'/shared/(.*)/(.*)', SharedEntityWithKeyHandler),
]
