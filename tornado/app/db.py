from tornado import database
from tornado.options import options

import logging
import hashlib

from collections import defaultdict


def formatDatetime(date, format='%(day)d.%(month)d.%(year)d %(hour)d:%(minute)d'):
    """
    Formats and returns date as string. Format tags are %(day)d, %(month)d, %(year)d, %(hour)d and %(minute)d.

    """
    return format % {'year': date.year, 'month': date.month, 'day': date.day, 'hour': date.hour, 'minute': date.minute}


class myDb():
    """
    Main database class. All database actions should go thru this.

    """
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

    def getEntityList(self, entity_id=None, search=None, only_public=True, entity_definition=None, user_id=None, limit=None):
        """
        Get list of Entities (with properties). entity_id, entity_definition and user_id can be single ID or list of IDs.

        """
        return self.getEntityProperties(entity_id=self.getEntityIdList(entity_id=entity_id, search=search, only_public=only_public, entity_definition=entity_definition, user_id=user_id, limit=limit), only_public=only_public)

    def getEntityIdList(self, entity_id=None, search=None, only_public=True, entity_definition=None, user_id=None, limit=None):
        """
        Get list of Entity IDs. entity_id, entity_definition and user_id can be single ID or list of IDs.

        """
        sql = 'SELECT STRAIGHT_JOIN DISTINCT bubble.id AS id FROM property_definition, property, bubble, relationship WHERE property.property_definition_id = property_definition.id AND bubble.id = property.bubble_id AND relationship.bubble_id = bubble.id'
        if entity_id:
            if type(entity_id) is not list:
                entity_id = [entity_id]
            sql += ' AND bubble.id IN (%s)' % ','.join(map(str, entity_id))

        if search:
            for s in search.split(' '):
                sql += ' AND value_string LIKE \'%%%%%s%%%%\'' % s

        if only_public == True:
            sql += ' AND property_definition.public = 1 AND bubble.public = 1'

        if entity_definition:
            if type(entity_definition) is not list:
                entity_definition = [entity_definition]
            sql += ' AND bubble.bubble_definition_id IN (%s)' % ','.join(map(str, entity_definition))

        if user_id:
            if type(user_id) is not list:
                user_id = [user_id]
            sql += ' AND relationship.related_bubble_id IN (%s) AND relationship.type IN (\'viewer\', \'editor\', \'owner\')' % ','.join(map(str, user_id))

        sql += ' ORDER BY bubble.id'

        if limit:
            sql += ' LIMIT %d' % limit

        sql += ';'
        # logging.info(sql)

        items = self.db.query(sql)
        if not items:
            return []
        return [x.id for x in items]

    def getEntityProperties(self, entity_id, only_public=True):
        """
        Get Entity properties. entity_id can be single ID or list of IDs.

        """
        if not entity_id:
            return []

        if type(entity_id) is not list:
            entity_id = [entity_id]

        if only_public == True:
            public = 'AND property_definition.public = 1 AND bubble.public = 1'
        else:
            public = ''

        sql = """
            SELECT
            bubble_definition.id AS entity_definition_id,
            bubble.id AS entity_id,
            property_definition.id AS property_definition_id,
            property.id AS property_id,

            bubble.created AS entity_created,

            bubble_definition.%(language)s_label AS entity_label,
            bubble_definition.%(language)s_label_plural AS entity_label_plural,
            bubble_definition.%(language)s_description AS entity_description,
            bubble_definition.%(language)s_displayname AS entity_displayname,
            bubble_definition.%(language)s_displayinfo AS entity_displayinfo,

            property_definition.%(language)s_fieldset AS property_fieldset,
            property_definition.%(language)s_label AS property_label,
            property_definition.%(language)s_label_plural AS property_label_plural,
            property_definition.%(language)s_description AS property_description,

            property.id AS property_id,
            property.value_string AS value_string,
            property.value_text AS value_text,
            property.value_integer AS value_integer,
            property.value_decimal AS value_decimal,
            property.value_boolean AS value_boolean,
            property.value_datetime AS value_datetime,
            property.value_reference AS value_reference,
            property.value_file AS value_file,
            property_definition.datatype AS property_datatype,
            property_definition.dataproperty AS property_dataproperty,
            property_definition.multiplicity AS property_multiplicity,
            property_definition.ordinal AS property_ordinal

            FROM
            bubble,
            bubble_definition,
            property,
            property_definition

            WHERE property.bubble_id = bubble.id
            AND bubble_definition.id = bubble.bubble_definition_id
            AND property_definition.id = property.property_definition_id
            AND bubble_definition.id = property_definition.bubble_definition_id
            AND (property.language = '%(language)s' OR property.language IS NULL)
            %(public)s
            AND bubble.id IN (%(idlist)s)
        """ % {'language': self.language, 'public': public, 'idlist': ','.join(map(str, entity_id))}
        # logging.info(sql)

        items = {}
        for row in self.db.query(sql):
            if not row.value_string and not row.value_text and not row.value_integer and not row.value_decimal and not row.value_boolean and not row.value_datetime and not row.value_reference and not row.value_file:
                continue

            #Entity
            items.setdefault('item_%s' % row.entity_id, {})['id'] = row.entity_id
            items.setdefault('item_%s' % row.entity_id, {})['label'] = row.entity_label
            items.setdefault('item_%s' % row.entity_id, {})['description'] = row.entity_description
            items.setdefault('item_%s' % row.entity_id, {})['created'] = row.entity_created
            items.setdefault('item_%s' % row.entity_id, {})['displayname'] = row.entity_displayname
            items.setdefault('item_%s' % row.entity_id, {})['displayinfo'] = row.entity_displayinfo

            #Property
            items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['id'] = row.property_id
            items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['label'] = row.property_label
            items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['description'] = row.property_description
            items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['datatype'] = row.property_datatype
            items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['dataproperty'] = row.property_dataproperty
            items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['multiplicity'] = row.property_multiplicity
            items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['ordinal'] = row.property_ordinal

            #Value
            if row.property_datatype in ['string', 'dictionary', 'dictionary_string', 'select', 'dictionary_select']:
                value = row.value_string
            elif row.property_datatype in ['text', 'dictionary_text']:
                value = row.value_text
            elif row.property_datatype == 'integer':
                value = row.value_integer
            elif row.property_datatype == 'float':
                value = row.value_decimal
            elif row.property_datatype == 'date':
                value = formatDatetime(row.value_datetime, '%(day)d.%(month)d.%(year)d')
            elif row.property_datatype == 'datetime':
                value = formatDatetime(row.value_datetime)
            elif row.property_datatype in ['reference']:
                value = row.value_reference
            elif row.property_datatype in ['blobstore']:
                blobstore = self.db.get('SELECT id, filename, filesize FROM file WHERE id=%s', row.value_file)
                value = blobstore.filename
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {}).setdefault('values', {}).setdefault('value_%s' % row.property_id, {})['file_id'] = blobstore.id
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {}).setdefault('values', {}).setdefault('value_%s' % row.property_id, {})['filesize'] = blobstore.filesize
            elif row.property_datatype in ['boolean']:
                value = row.value_boolean
            elif row.property_datatype in ['counter']:
                value = row.value_reference
            else:
                value = 'X'

            items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {}).setdefault('values', {}).setdefault('value_%s' % row.property_id, {})['value'] = value
            items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {}).setdefault('values', {}).setdefault('value_%s' % row.property_id, {})['id'] = row.property_id

        return items.values()

    def getFile(self, file_id, only_public=True):
        """
        Returns file object. Properties are id, file, filename

        """
        if only_public == True:
            publicsql = 'AND property_definition.public = 1'
        else:
            publicsql = ''

        sql = """
            SELECT
            file.id,
            file.file,
            file.filename
            FROM
            file,
            property,
            property_definition
            WHERE property.value_file = file.id
            AND property_definition.id = property.property_definition_id
            AND file.id = %(file_id)s
            %(public)s
            LIMIT 1
            """ % {'file_id': file_id, 'public': publicsql}
        # logging.info(sql)

        return self.db.get(sql)

    def getEntityImage(self, id):
        return 'http://www.gravatar.com/avatar/%s?d=identicon' % (hashlib.md5(str(id)).hexdigest())

    def getMenu(self, user_id):
        """
        Returns user menu.

        """

        sql = """
            SELECT DISTINCT
            bubble_definition.id,
            bubble_definition.%(language)s_menu AS menugroup,
            bubble_definition.%(language)s_label AS item
            FROM
            bubble_definition,
            bubble,
            relationship
            WHERE bubble.bubble_definition_id = bubble_definition.id
            AND relationship.bubble_id = bubble.id
            AND relationship.type IN ('viewer', 'editor', 'owner')
            AND bubble_definition.estonian_menu IS NOT NULL
            AND relationship.related_bubble_id = %(user_id)s
            ORDER BY
            bubble_definition.estonian_menu,
            bubble_definition.estonian_label;
        """ % {'language': self.language, 'user_id': user_id}
        # logging.info(sql)

        menu = {}
        for m in self.db.query(sql):
            menu.setdefault(m.menugroup, []).append({'id': m.id, 'title': m.item})
        return menu
