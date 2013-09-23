# -*- coding: utf-8 -*-

from tornado import auth
from tornado import web
from operator import itemgetter
from PyZ3950 import zoom

import logging
import json


from main.helper import *
from main.db import *

#http://www.loc.gov/marc/bibliographic/
MARCMAP = {
     '20a': 'isn',
     '22a': 'isn',
     '41a': 'language',
     '41h': 'original-language',
     '72a': 'udc',
     '80a': 'udc',
    '100a': 'author',
    '245a': 'title',
    '245b': 'subtitle',
    '245p': 'subtitle',
    '245n': 'number',
    '250a': 'edition',
    '260a': 'publishing-place',
    '260b': 'publisher',
    '260c': 'publishing-date',
    '300a': 'pages',
    '300c': 'dimensions',
    '440a': 'series',
    '440p': 'series',
    '440n': 'series-number',
    '440v': 'series-number',
    '500a': 'notes',
    '501a': 'notes',
    '502a': 'notes',
    '504a': 'notes',
    '505a': 'notes',
    '520a': 'notes',
    '525a': 'notes',
    '530a': 'notes',
    '650a': 'tag',
    '655a': 'tag',
    '907a': 'ester-id',
}

AUTHORMAP = {
    u'fotograaf':        'photographer',
    u'illustreerija':    'illustrator',
    u'järelsõna autor':  'epilogue-author',
    u'koostaja':         'compiler',
    u'kujundaja':        'designer',
    u'toimetaja':        'editor',
    u'tõlkija':          'translator',
    u'tolkija':          'translator',
}

class EsterSearch(myRequestHandler, Entity):
    """
    """
    @web.authenticated
    def post(self):
        search_term = self.get_argument('query', default='', strip=True)
        if not search_term:
            return

        search_term = search_term.encode('utf-8').replace('http://tallinn.ester.ee/record=', '').replace('~S1*est', '')

        conn = zoom.Connection('tallinn.ester.ee', 212)
        conn.databaseName = 'INNOPAC'
        conn.preferredRecordSyntax = 'USMARC'

        query = zoom.Query('PQF', '@or @attr 1=4 "%(st)s" @or @attr 1=7 "%(st)s" @attr 1=12 "%(st)s"' % {'st': search_term})
        res = conn.search(query)

        results = []
        for r in res:
            results.append('%s' % r)
        results = list(set(results))

        items = []
        for i in results:
            item = ParseMARC(i)

            file_name = 'ester-%s' % item.get('ester-id', [''])[0]
            file_id = self.db.execute_lastrowid('INSERT INTO tmp_file SET filename = %s, file = %s, created_by = %s, created = NOW();', file_name, json.dumps(item), self.current_user.id)

            entity = GetExistingID(self, item.get('ester-id', [''])[0])

            items.append({
                'file_id': file_id,
                'entity_id': entity.get('entity_id'),
                'entity_definition_keyname': entity.get('entity_definition_keyname'),
                'title': item.get('title'),
                'subtitle': item.get('subtitle'),
                'author': item.get('author'),
                'year': item.get('publishing-date'),
                'isbn': item.get('isn'),
            })

        self.write({'items': sorted(items, key=itemgetter('title', 'year'))})


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
        entity = GetExistingID(self, item.get('ester-id', [''])[0])

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
    entity = rh.db.get('SELECT property.entity_id, entity.entity_definition_keyname FROM property, entity, property_definition WHERE entity.id = property.entity_id AND property_definition.keyname = property.property_definition_keyname AND property_definition.dataproperty = \'ester-id\' AND property.value_string = %s AND property.is_deleted = 0 AND entity.is_deleted = 0 LIMIT 1', ester_id)
    if not entity:
        return {}

    return entity


def ParseMARC(data):
    marc = {}
    result = {}
    for row in data.strip().split('\n')[1:]:
        key = row.split(' ')[0]
        start = row.find('$')
        if start < 0:
            continue
        values = row[start+1:].split('$')

        kv = {}
        for v in values:
            if not v:
                continue
            kv.setdefault(v[0], []).append(CleanData(v[1:], key+v[0]))
        marc.setdefault(key, []).append(kv)

    for k1, ml in marc.iteritems():
        for m in ml:
            if k1 == '700' and m.get('a'):
                result.setdefault(AUTHORMAP.get(m.get('e', [''])[0], m.get('e', ['author'])[0]), []).append(m.get('a', [''])[0])
            else:
                for k2, v in m.iteritems():
                    if not MARCMAP.get(k1+k2):
                        continue
                    for i in v:
                        result.setdefault(MARCMAP.get(k1+k2), []).append(i)
    return result


def CleanData(value, tag=None):
    value = value.decode('utf-8').strip(' /,;:')
    if value[0:1] == '[' and value[-1] == ']':
        value = value[1:][:-1]
    if tag == '260c' and not value[0:1].isdigit():
        value = value[1:]
    if tag == '907a':
        value = value.strip('.')
    return value


handlers = [
    ('/action/ester/search', EsterSearch),
    ('/action/ester/import', EsterImport),
]
