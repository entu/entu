from tornado import database
from tornado.options import options

import logging

from collections import defaultdict

class myDb():
    def __init__(self, language='estonian'):
        self.language = language

    @property
    def db(self):
        return database.Connection(
            host        = options.mysql_host,
            database    = options.mysql_database,
            user        = options.mysql_user,
            password    = options.mysql_password,
        )

    def getBubbleList(self, id=None, search=None, only_public=True, bubble_definition=None, limit=None):
        sql = 'SELECT DISTINCT bubble.id FROM property_definition, property, bubble WHERE property.property_definition_id = property_definition.id AND bubble.id = property.bubble_id'
        if id:
            if type(id) is not list:
                id = [id]
            sql += ' AND bubble.id IN (%s)' % ','.join(map(str, id))

        if search:
            for s in search.split(' '):
                sql += ' AND value_string LIKE \'%%%%%s%%%%\'' % s

        if only_public == True:
            publicsql = ' AND property_definition.public = 1 AND bubble.public = 1'
            sql += publicsql

        if bubble_definition:
            if type(bubble_definition) is not list:
                bubble_definition = [bubble_definition]
            sql += ' AND bubble.bubble_definition_id IN (%s)' % ','.join(map(str, bubble_definition))

        if limit:
            sql += ' LIMIT %d' % limit

        sql += ';'

        logging.warning(sql)
        itemlist = self.db.query(sql)
        if not itemlist:
            return []

        logging.info(sql)
        idlist = ','.join([str(x.id) for x in itemlist])

        sql = """
            SELECT
            bubble_definition.id AS bubble_definition_id,
            bubble.id AS bubble_id,
            property_definition.id AS property_definition_id,
            property.id AS property_id,

            bubble.created AS bubble_created,

            bubble_definition.%(language)s_label AS bubble_label,
            bubble_definition.%(language)s_label_plural AS bubble_label_plural,
            bubble_definition.%(language)s_description AS bubble_description,

            property_definition.%(language)s_fieldset AS property_fieldset,
            property_definition.%(language)s_label AS property_label,
            property_definition.%(language)s_label_plural AS property_label_plural,
            property_definition.%(language)s_description AS property_description,

            property.id AS property_id,
            IF(property_definition.datatype='string',
                value_string,
                IF(property_definition.datatype='text',
                    value_text,
                    IF(property_definition.datatype='integer',
                        value_integer,
                        IF(property_definition.datatype='decimal',
                            value_decimal,
                            IF(property_definition.datatype='boolean',
                                value_boolean,
                                IF(property_definition.datatype='datetime' OR property_definition.datatype='date',
                                    value_datetime,
                                    NULL
                                )
                            )
                        )
                    )
                )
            ) AS property_value,
            property.value_datetime AS value_datetime,
            property_definition.datatype AS property_datatype,
            property_definition.dataproperty AS property_dataproperty,
            property_definition.multiplicity AS property_multiplicity,
            property_definition.ordinal AS property_ordinal

            FROM
            bubble,
            bubble_definition,
            property,
            property_definition
            WHERE 1=1
            #AND bubble_definition.id = bubble.bubble_definition_id
            AND property.bubble_id = bubble.id
            AND property_definition.id = property.property_definition_id
            AND bubble_definition.id = property_definition.bubble_definition_id
            #AND property_definition.datatype = 'date'
            %(public)s
            AND bubble.id IN (%(search)s)
        """ % {'language': self.language, 'public': publicsql, 'search': idlist}

        items = {}
        for row in self.db.query(sql):
            if not row.property_value:
                continue

            #Item
            items.setdefault('item_%s' % row.bubble_id, {})['id'] = row.bubble_id
            items.setdefault('item_%s' % row.bubble_id, {})['label'] = row.bubble_label
            items.setdefault('item_%s' % row.bubble_id, {})['description'] = row.bubble_description
            items.setdefault('item_%s' % row.bubble_id, {})['created'] = row.bubble_created
            #Property
            items.setdefault('item_%s' % row.bubble_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['id'] = row.property_id
            items.setdefault('item_%s' % row.bubble_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['label'] = row.property_label
            items.setdefault('item_%s' % row.bubble_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['description'] = row.property_description
            items.setdefault('item_%s' % row.bubble_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['datatype'] = row.property_datatype
            items.setdefault('item_%s' % row.bubble_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['dataproperty'] = row.property_dataproperty
            items.setdefault('item_%s' % row.bubble_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['multiplicity'] = row.property_multiplicity
            items.setdefault('item_%s' % row.bubble_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['ordinal'] = row.property_ordinal
            #Value
            items.setdefault('item_%s' % row.bubble_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {}).setdefault('values', {}).setdefault('value_%s' % row.property_id, {})['id'] = row.property_id
            if row.property_datatype in ['date', 'datetime']:
                value = row.value_datetime.strftime('%d.%m.%Y')
            else:
                value = row.property_value
            items.setdefault('item_%s' % row.bubble_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {}).setdefault('values', {}).setdefault('value_%s' % row.property_id, {})['value'] = value

        return items.values()

    def getBubblePublicKey(id):
        pass

