from tornado import web, gen, httpclient

import logging
import json
import urllib


from main.helper import *
from main.db import *


class EsterCheckIfExists(myRequestHandler):
    @web.removeslash
    def get(self):
        if not self.current_user:
            self.json({
                'error': 'Forbidden!',
                'time': round(self.request.request_time(), 3)
            }, 403)
            return

        ester_id = self.get_argument('ester_id', default='', strip=True).strip('bx. ')[:7]
        if not ester_id:
            self.json({
                'error': 'No ester ID!',
                'time': round(self.request.request_time(), 3)
            }, 400)
            return

        sql = """
            SELECT
                '%s' AS id,
                property.entity_id AS entity,
                entity.entity_definition_keyname AS definition
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
        """ % (self.get_argument('id', default='', strip=True), ester_id)
        # logging.warning(sql)

        entity = self.db_get(sql)
        if entity:
            self.json({
                'result': entity,
                'time': round(self.request.request_time(), 3)
            })
        else:
            self.json({
                'time': round(self.request.request_time(), 3)
            }, 404)


class EsterImport(myRequestHandler, Entity):
    @web.removeslash
    @gen.coroutine
    def post(self):
        if not self.current_user:
            self.json({
                'error': 'Forbidden!',
                'time': round(self.request.request_time(), 3)
            }, 403)
            return

        id = self.get_argument('id', default=None, strip=True)
        entity = self.get_argument('entity', default=None, strip=True)
        definition = self.get_argument('definition', default=None, strip=True)

        if not id or not entity or not definition:
            return

        http_client = httpclient.AsyncHTTPClient()
        ester_request = yield http_client.fetch(httpclient.HTTPRequest(
            url='https://ester.entu.ee/item/%s?f=human' % id,
            method='GET',
            request_timeout=60
        ))

        try:
            ester = json.loads(ester_request.body)
        except Exception:
            self.json({
                'error': 'Ester proxy failed!',
                'time': round(self.request.request_time(), 3),
            }, 500)
            return

        item = ester['result']
        entity_id = self.create_entity(entity_definition_keyname=definition, parent_entity_id=entity)

        for field, values in item.iteritems():
            sql = 'SELECT keyname FROM property_definition WHERE dataproperty = \'%s\' COLLATE utf8_general_ci AND entity_definition_keyname = \'%s\' LIMIT 1;' % (field, definition)

            property_definition = self.db_get(sql)
            if not property_definition:
                logging.warning('%s: %s' % (field, values))
                continue

            if type(values) is not list:
                values = [values]
            for value in values:
                self.set_property(entity_id=entity_id, property_definition_keyname=property_definition.get('keyname'), value=value)

        self.write(str(entity_id))


handlers = [
    (r'/ester/check', EsterCheckIfExists),
    (r'/ester/import', EsterImport),
]
