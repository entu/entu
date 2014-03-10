# -*- coding: utf-8 -*-

from tornado import auth, web
from operator import itemgetter
from PyZ3950 import zoom, zmarc

import datetime
import logging
import json


from main.helper import *
from main.db import *


class ESTER():
    server = 'tallinn.ester.ee'
    port = 212
    database = 'INNOPAC'

    __raw = []
    __marc = []
    __human = []

    __marcmapping = { #http://www.loc.gov/marc/bibliographic
         20: {'a': 'isn'},
         22: {'a': 'isn'},
         41: {'a': 'language',
              'h': 'original-language'},
         72: {'a': 'udc'},
         80: {'a': 'udc'},
        100: {'a': 'author'},
        245: {'a': 'title',
              'b': 'subtitle',
              'p': 'subtitle',
              'n': 'number'},
        250: {'a': 'edition'},
        260: {'a': 'publishing-place',
              'b': 'publisher',
              'c': 'publishing-date'},
        300: {'a': 'pages',
              'c': 'dimensions'},
        440: {'a': 'series',
              'p': 'series',
              'n': 'series-number',
              'v': 'series-number'},
        500: {'a': 'notes'},
        501: {'a': 'notes'},
        502: {'a': 'notes'},
        504: {'a': 'notes'},
        505: {'a': 'notes'},
        520: {'a': 'notes'},
        525: {'a': 'notes'},
        530: {'a': 'notes'},
        650: {'a': 'tag'},
        655: {'a': 'tag'},
        710: {'a': 'publisher'},
        907: {'a': 'ester-id'},
    }

    __authormapping = {
        u'fotograaf':        'photographer',
        u'helilooja':        'composer',
        u'illustreerija':    'illustrator',
        u'järelsõna autor':  'epilogue-author',
        u'koostaja':         'compiler',
        u'kujundaja':        'designer',
        u'osatäitja':        'actor',
        u'produtsent':       'producer',
        u'režissöör':        'director',
        u'stsenarist':       'screenwriter',
        u'toimetaja':        'editor',
        u'tolkija':          'translator',
        u'tõlkija':          'translator',
    }

    def __init__(self, server=None, port=None, database=None):
        if server:
            self.server = server
        if port:
            self.port = port
        if database:
            self.database = database

    def __len__(self):
        return len(self.__raw)

    def search(self, query):
        self.__raw = []
        self.__marc = []
        self.__human = []

        try:
            ester_conn = zoom.Connection(self.server, self.port)
            ester_conn.databaseName = self.database
            ester_conn.preferredRecordSyntax = 'USMARC'
            ester_query = zoom.Query('PQF', '@or @attr 1=4 "%(st)s" @or @attr 1=7 "%(st)s" @attr 1=12 "%(st)s"' % {'st': query})
            ester_result = ester_conn.search(ester_query)

            logging.debug('Found %s results for "%s" in %s:%s/%s' % (len(ester_result), query, self.server, self.port, self.database))

            if len(ester_result) > 0:
                for r in ester_result:
                    self.__raw.append(r.data)

        except Exception, e:
            logging.error('e: %s q:%s' % (e, query))

        ester_conn.close()

    def raw(self):
        return self.__raw

    def marc(self):
        if self.__marc:
            return self.__marc

        for raw in self.__raw:
            item = {}
            for tag, tag_values in zmarc.MARC(raw).fields.iteritems():
                for v in tag_values:
                    if type(v) is not tuple:
                        item = self.__add_to_dict(item, tag, v)
                    else:
                        if len(v) == 3:
                            value = {}
                            for i in v[2]:
                                if len(i) == 2:
                                    value = self.__add_to_dict(value, i[0], i[1])
                            item = self.__add_to_dict(item, tag, value)
                        else:
                            item = self.__add_to_dict(item, tag, v)
            self.__marc.append(item)

        logging.debug('Converted %s raw records to marc dictionary' % len(self.__raw))
        return self.__marc

    def human(self):
        if self.__human:
            return self.__human

        for marc in self.marc():
            item = {}
            for tag, tag_values in marc.iteritems():
                if type(tag_values) is not list:
                    tag_values = [tag_values]
                for tag_value in tag_values:
                    if type(tag_value) is not dict:
                        tag_value = {'x': tag_value}
                    for attr, values in tag_value.iteritems():
                        if type(values) is not list:
                            values = [values]
                        for v in values:
                            if self.__marcmapping.get(tag, {}).get(attr):
                                item = self.__add_to_dict(item, self.__marcmapping.get(tag, {}).get(attr), v.decode('utf-8').strip(' /,;:'))
                            elif tag == 5:
                                try:
                                    item = self.__add_to_dict(item, 'ester-changed-date', datetime.datetime.strptime(self.__clean_str(v)[:14], '%Y%m%d%H%M%S'))
                                except Exception, e:
                                    pass
                            elif tag == 700:
                                if self.__clean_str(tag_value.get('e'), '.') in self.__authormapping.keys() + self.__authormapping.values():
                                    item = self.__add_to_dict(item, self.__authormapping.get(self.__clean_str(tag_value.get('e'), '.'), self.__clean_str(tag_value.get('e'), '.')), tag_value.get('a'))
            self.__human.append(item)

        logging.debug('Converted %s marc records to human dictionary' % len(self.__marc))
        return self.__human

    def __clean_str(self, str, stripstr=''):
        if str:
            return str.decode('utf-8').strip(' /,;:%s' % stripstr)

    def __add_to_dict(self, dictionary, key, value):
        if key in dictionary:
            if type(dictionary[key]) is not list:
                dictionary[key] = [dictionary[key]]
            if value not in dictionary[key]:
                dictionary[key].append(value)
        else:
            dictionary[key] = value

        return dictionary


class EsterTest(myRequestHandler, Entity):
    """
    """
    def get(self):
        query = self.get_argument('query', default=0, strip=True)
        query = query.encode('utf-8').replace('http://tartu.ester.ee/record=', '').replace('http://tallinn.ester.ee/record=', '').replace('~S1*est', '')

        ester = ESTER()
        ester.search(query)

        self.json({
            'raw': ester.raw(),
            'marc': ester.marc(),
            'human': ester.human(),
            'count': len(ester),
            'time': self.request.request_time(),
        })


class EsterSearch(myRequestHandler, Entity):
    """
    """
    @web.authenticated
    def post(self):
        query = self.get_argument('query', default=0, strip=True)
        query = query.encode('utf-8').replace('http://tartu.ester.ee/record=', '').replace('http://tallinn.ester.ee/record=', '').replace('~S1*est', '')

        ester = ESTER()
        ester.search(query)

        items = []
        for item in ester.human():
            file_name = 'ester-%s' % item.get('ester-id')
            file_json = json.dumps(item, cls=JSONDateFix)
            file_id = self.db.execute_lastrowid('INSERT INTO tmp_file SET filename = %s, filesize = %s, file = %s, created_by = %s, created = NOW();', file_name, len(file_json), file_json, self.current_user.id)

            entity = GetExistingID(self, item.get('ester-id'))

            items.append({
                'file_id': file_id,
                'entity_id': entity.get('entity_id'),
                'entity_definition_keyname': entity.get('entity_definition_keyname'),
                'title': item.get('title') if not item.get('title') or type(item.get('title')) is list else [item.get('title')],
                'subtitle': item.get('subtitle') if not item.get('subtitle') or type(item.get('subtitle')) is list else [item.get('subtitle')],
                'author': item.get('author') if not item.get('author') or type(item.get('author')) is list else [item.get('author')],
                'year': item.get('publishing-date') if not item.get('publishing-date') or type(item.get('publishing-date')) is list else [item.get('publishing-date')],
                'isbn': item.get('isn') if not item.get('isn') or type(item.get('isn')) is list else [item.get('isn')],
            })

        self.json({'items': sorted(items, key=itemgetter('title', 'year'))})


class EsterImport(myRequestHandler, Entity):
    """
    """
    @web.authenticated
    def post(self):
        file_id                   = self.get_argument('file_id', default=None, strip=True)
        parent_entity_id          = self.get_argument('parent_entity_id', default=None, strip=True)
        entity_definition_keyname = self.get_argument('entity_definition_keyname', default=None, strip=True)

        if not file_id or not parent_entity_id or not entity_definition_keyname:
            return

        tmp_file = self.db.get('SELECT file FROM tmp_file WHERE id = %s LIMIT 1;', file_id)
        if not tmp_file:
            return

        if not tmp_file.file:
            return

        item = json.loads(tmp_file.file)
        entity = GetExistingID(self, item.get('ester-id'))

        if entity.get('entity_id'):
            return self.write(str(entity.get('entity_id')))

        entity_id = self.create_entity(entity_definition_keyname=entity_definition_keyname, parent_entity_id=parent_entity_id)

        for field, values in item.iteritems():
            sql = 'SELECT keyname FROM property_definition WHERE dataproperty = \'%s\' COLLATE utf8_general_ci AND entity_definition_keyname = \'%s\' LIMIT 1;' % (field, entity_definition_keyname)

            property_definition = self.db.get(sql)
            if not property_definition:
                logging.warning('%s: %s' % (field, values))
                continue

            if type(values) is not list:
                values = [values]
            for value in values:
                self.set_property(entity_id=entity_id, property_definition_keyname=property_definition.keyname, value=value)

        self.write(str(entity_id))


def GetExistingID(rh, ester_id):
    sql = """
        SELECT
            property.entity_id,
            entity.entity_definition_keyname
        FROM
            property,
            entity,
            property_definition
        WHERE entity.id = property.entity_id
        AND property_definition.keyname = property.property_definition_keyname
        AND property_definition.dataproperty = 'ester-id'
        AND LEFT(REPLACE(REPLACE(REPLACE(property.value_string, '.', ''), 'b', ''), ' ', ''), 7) = '%s'
        AND property.is_deleted = 0
        AND entity.is_deleted = 0
        AND property_definition.is_deleted = 0
        LIMIT 1;
    """ % ester_id.strip('bx. ')[:7]
    # logging.warning(sql)

    entity = rh.db.get(sql)
    if not entity:
        return {}

    return entity


handlers = [
    ('/library/ester', EsterTest),
    ('/action/ester/search', EsterSearch),
    ('/action/ester/import', EsterImport),
]
