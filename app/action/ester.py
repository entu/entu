# -*- coding: utf-8 -*-

from tornado import auth
from tornado import web
from tornado import httpclient
from bs4 import BeautifulSoup

import logging

from HTMLParser import HTMLParser
# from urllib import quote

import db
from helper import *

#http://www.loc.gov/marc/bibliographic/
MARCMAP = {
    '020':  'isn',
    '022':  'isn',
    '041':  'language',
    '041h': 'original-language',
    '072':  'udc',
    '080':  'udc',
    '100':  'author',
    '245':  'title',
    '245b': 'subtitle',
    '245p': 'subtitle',
    '245n': 'number',
    '250':  'edition',
    '260':  'publishing-place',
    '260b': 'publisher',
    '260c': 'publishing-date',
    '300':  'pages',
    '300c': 'dimensions',
    '440':  'series',
    '440p': 'series',
    '440n': 'series-number',
    '440v': 'series-number',
    '500':  'notes',
    '501':  'notes',
    '502':  'notes',
    '504':  'notes',
    '505':  'notes',
    '520':  'notes',
    '525':  'notes',
    '530':  'notes',
    '650':  'tag',
    '655':  'tag',
}

AUTHORMAP = {
    u'fotograaf':        'photographer',
    u'illustreerija':    'illustrator',
    u'järelsõna autor':  'epilogue-author',
    u'koostaja':         'compiler',
    u'kujundaja':        'designer',
    u'toimetaja':        'editor',
    u'tõlkija':          'translator',
}

class EsterSearch(myRequestHandler):
    """
    """
    @web.authenticated
    @web.asynchronous
    def post(self):
        search_term = self.get_argument('query', default='', strip=True)
        if not search_term:
            return

        search_isbn = False
        if len(search_term) == 10 and search_term[:9].isdigit():
            search_isbn = True
        if len(search_term) == 13 and search_term.isdigit():
            search_isbn = True

        if search_isbn == True:
            url = 'http://tallinn.ester.ee/search*est/i?SEARCH=%s&searchscope=1&SUBMIT=OTSI' % search_term
        else:
            url = 'http://tallinn.ester.ee/search*est/X?SEARCH=%s&searchscope=1&SUBMIT=OTSI' % search_term

        response = httpclient.AsyncHTTPClient().fetch(url, callback=self._got_list)

    @web.asynchronous
    def _got_list(self, response):
        soup = BeautifulSoup(response.body.decode('utf-8','ignore'))

        items = []
        id = soup.find('a', attrs={'id': 'recordnum'})
        if id:
            id = id['href'].replace('http://tallinn.ester.ee/record=', '').replace('~S1', '').replace('*est', '').strip()
            httpclient.AsyncHTTPClient().fetch('http://tallinn.ester.ee/search~S1?/.'+id+'/.'+id+'/1,1,1,B/marc~'+id, callback=self._got_one)
        else:
            for i in soup.find_all('table', class_='browseList'):
                cells = i.find_all('td')
                ester_id = cells[0].input['value'].strip()
                title = cells[1].span.a.contents[0].strip()
                isbn = cells[1].find(text='ISBN/ISSN').next.strip(':&nbsp;\n ').strip()
                year = cells[4].contents[0].strip().strip('c')
                entity = GetExistingID(ester_id)
                items.append({
                    'id': ester_id,
                    'entity_id': entity.get('entity_id'),
                    'entity_definition_keyname': entity.get('entity_definition_keyname'),
                    'isbn': [isbn],
                    'title': [title],
                    'publishing_date': [year],
                })
            self.write({'items': items})
            self.finish()

    @web.asynchronous
    def _got_one(self, response):
        marc = response.body.split('<pre>')[1].split('</pre>')[0].strip()
        # item = ParseMARC(HTMLParser().unescape((marc))
        item = ParseMARC(marc)
        ester_id = response.effective_url.split('/marc~')[1]
        entity = GetExistingID(ester_id)

        items = []
        items.append({
            'id': ester_id,
            'entity_id': entity.get('entity_id'),
            'entity_definition_keyname': entity.get('entity_definition_keyname'),
            'isbn': item.get('isn', []),
            'title': ['%s / %s' % (item.get('title', [''])[0], item.get('author', [''])[0])],
            'publishing_date': item.get('publishing-date', []),
        })

        self.write({'items': items})
        self.finish()


class EsterImport(myRequestHandler):
    """
    """
    @web.authenticated
    def post(self):
        ester_id                  = self.get_argument('ester_id', default=None, strip=True)
        parent_entity_id          = self.get_argument('parent_entity_id', default=None, strip=True)
        entity_definition_keyname = self.get_argument('entity_definition_keyname', default=None, strip=True)
        if not ester_id or not parent_entity_id or not entity_definition_keyname:
            return

        entity = GetExistingID(ester_id)
        if entity.get('entity_id'):
            return self.write(str(entity.get('entity_id')))

        response = httpclient.HTTPClient().fetch('http://tallinn.ester.ee/search~S1?/.'+ester_id+'/.'+ester_id+'/1,1,1,B/marc~'+ester_id)

        marc = response.body.split('<pre>')[1].split('</pre>')[0].strip()
        # item = ParseMARC(HTMLParser().unescape((marc))
        item = ParseMARC(marc)
        if not item:
            return

        item['ester-id'] = ester_id

        db_connection = db.connection()

        logging.debug(str(item))

        entity = db.Entity(user_locale=self.get_user_locale(), user_id=self.current_user.id)
        entity_id = entity.create(entity_definition_keyname=entity_definition_keyname, parent_entity_id=parent_entity_id)

        for field, values in item.iteritems():
            sql = 'SELECT keyname FROM property_definition WHERE dataproperty = \'%s\' AND entity_definition_keyname = \'%s\' LIMIT 1;' % (field, entity_definition_keyname)
            logging.debug(sql)

            property_definition = db_connection.get(sql)
            if not property_definition:
                logging.warning('%s: %s' % (field, values))
                continue

            if type(values) is not list:
                values = [values]
            for value in values:
                entity.set_property(entity_id=entity_id, property_definition_keyname=property_definition.keyname, value=value)

        self.write(str(entity_id))


class EsterTest(myRequestHandler):
    """
    """
    @web.authenticated
    def get(self, ester_id):
        response = httpclient.HTTPClient().fetch('http://tallinn.ester.ee/search~S1?/.'+ester_id+'/.'+ester_id+'/1,1,1,B/marc~'+ester_id)

        marc = response.body.split('<pre>')[1].split('</pre>')[0].strip()
        self.write(ParseMARC(marc))


def GetExistingID(ester_id):
    db_connection = db.connection()
    entity = db_connection.get('SELECT property.entity_id, entity.entity_definition_keyname FROM property, entity, property_definition WHERE entity.id = property.entity_id AND property_definition.keyname = property.property_definition_keyname AND property_definition.dataproperty = \'ester-id\' AND property.value_string = %s AND property.deleted IS NULL LIMIT 1', ester_id)
    if not entity:
        return {}

    return entity


def ParseMARC(data):
    result = {}
    rows = []
    rownum = 0
    for row in data.strip().split('\n'):
        if row[:7].strip():
            rownum += 1
            rows.append(row)
        else:
            rows[rownum-1] += row[7:]

    for row in rows:
        key = row[:3]
        values = row[7:].split('|')

        if key in ['700']:
            if values[0]:
                tag = 'author'
                tag_value = CleanData(values[0])
                for v in values[1:]:
                    if v:
                        if v[0] == 'e':
                            tag = CleanData(v[1:])
                            if tag in AUTHORMAP:
                                tag = AUTHORMAP[tag]
                            else:
                                tag = toURL(tag)
                if tag not in result:
                    result[tag] = []
                result[tag].append(tag_value)
        else:
            if values[0]:
                if key in MARCMAP:
                    tag = MARCMAP[key]
                    if tag not in result:
                        result[tag] = []
                    result[tag].append(CleanData(values[0], tag))
            for v in values[1:]:
                if v:
                    if key+v[0] in MARCMAP:
                        tag = MARCMAP[key+v[0]]
                        if tag not in result:
                            result[tag] = []
                        result[tag].append(CleanData(v[1:], tag))
    return result


def CleanData(value, tag=None):
    value = value.decode('utf-8').strip(' /,;:')
    if value[0:1] == '[' and value[-1] == ']':
        value = value[1:][:-1]
    if tag == 'publishing-date' and not value[0:1].isdigit():
        value = value[1:]
    return value


def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)


def GetType(record):

    if '000' in record:
        a = record['000'][0]['a'][6:7]
        b = record['000'][0]['a'][7:8]

        if a == 'a':
            if 'acdm'.find(b) > 0:
                return 'book'
            if 'bis'.find(b) > 0:
                return 'series'

        if a == 't':
            return 'book'

        if a == 'p':
            return 'mixed'

        if a == 'm':
            return 'file'

        if 'ef'.find(a) > 0:
            return 'map'

        if 'gkor'.find(a) > 0:
            return 'visual'

        if 'sdij'.find(a) > 0:
            return 'music'


handlers = [
    ('/action/ester/search', EsterSearch),
    ('/action/ester/import', EsterImport),
    ('/action/ester/test/(.*)', EsterTest),
]
