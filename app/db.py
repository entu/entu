from tornado import database
from tornado import locale
from tornado.options import options

from operator import itemgetter
from datetime import datetime

import logging
import hashlib
import re


def connection():
    """
    Returns DB connection.

    """
    return database.Connection(
        host        = options.mysql_host,
        database    = options.mysql_database,
        user        = options.mysql_user,
        password    = options.mysql_password,
    )


class Entity():
    """
    Entity class. user_id can be single ID or list of IDs. If user_id is not set all Entity class methods will return only public stuff.
    """
    def __init__(self, user_locale, user_id=None):
        self.db             = connection()

        self.user_id        = user_id
        self.user_locale    = user_locale
        self.language       = user_locale.code
        self.created_by   = ''

        if user_id:
            if type(self.user_id) is not list:
                self.user_id = [self.user_id]
            self.created_by = ','.join(map(str, self.user_id))

    def create(self, entity_definition_keyname, parent_entity_id=None):
        """
        Creates new Entity and returns its ID.

        """
        if not entity_definition_keyname:
            return

        # Create entity
        sql = """
            INSERT INTO entity SET
                entity_definition_keyname = %s,
                created_by = %s,
                created = NOW();
        """
        # logging.debug(sql)
        entity_id = self.db.execute_lastrowid(sql, entity_definition_keyname, self.created_by)

        if not parent_entity_id:
            return entity_id

        # Insert child relationship
        sql = """
            INSERT INTO relationship SET
                relationship_definition_keyname = 'child',
                entity_id = %s,
                related_entity_id = %s,
                created_by = %s,
                created = NOW();
        """
        # logging.debug(sql)
        self.db.execute(sql, parent_entity_id, entity_id, self.created_by)

        # Copy user rights
        sql = """
            INSERT INTO relationship (
                relationship_definition_keyname,
                entity_id,
                related_entity_id,
                created_by,
                created
            ) SELECT /* SQL_NO_CACHE */
                relationship_definition_keyname,
                %s,
                related_entity_id,
                %s,
                NOW()
            FROM
                relationship
            WHERE relationship_definition_keyname IN ('leecher', 'viewer', 'editor', 'owner')
            AND entity_id = %s;
        """
        # logging.debug(sql)
        self.db.execute(sql, entity_id, self.created_by, parent_entity_id)

        # Propagate properties
        sql = """
            INSERT INTO property (
                entity_id,
                property_definition_keyname,
                language,
                value_string,
                value_text,
                value_integer,
                value_decimal,
                value_boolean,
                value_datetime,
                value_entity,
                value_file,
                value_counter,
                created_by,
                created
            ) SELECT /* SQL_NO_CACHE */
                %s,
                relationship.related_property_definition_keyname,
                property.language,
                property.value_string,
                property.value_text,
                property.value_integer,
                property.value_decimal,
                property.value_boolean,
                property.value_datetime,
                property.value_entity,
                property.value_file,
                property.value_counter,
                %s,
                NOW()
            FROM
                relationship,
                property_definition,
                property
            WHERE property_definition.keyname = relationship.property_definition_keyname
            AND property.property_definition_keyname = property_definition.keyname
            AND property_definition.entity_definition_keyname = %s
            AND property.entity_id = %s
            AND relationship.relationship_definition_keyname = 'propagated_property';
        """
        # logging.debug(sql)
        self.db.execute(sql, entity_id, self.created_by, entity_definition_keyname, parent_entity_id)

        return entity_id

    def set_property(self, entity_id=None, relationship_id=None, property_definition_keyname=None, value=None, property_id=None, uploaded_file=None):
        """
        Saves property value. Creates new one if property_id = None. Returns property ID.

        """
        if not entity_id and not relationship_id:
            return

        if not property_definition_keyname:
            return

        definition = self.db.get('SELECT datatype FROM property_definition WHERE keyname = %s LIMIT 1;', property_definition_keyname)

        if not definition:
            return

        if definition.datatype in ['text', 'html']:
            field = 'value_text'
        elif definition.datatype == 'integer':
            field = 'value_integer'
        elif definition.datatype == 'decimal':
            field = 'value_decimal'
            value = value.replace(',', '.')
            value = re.sub(r'[^\.0-9:]', '', value)
            if not value:
                value = 0.0
        elif definition.datatype == 'date':
            field = 'value_datetime'
        elif definition.datatype == 'datetime':
            field = 'value_datetime'
        elif definition.datatype == 'file':
            value = 0
            if uploaded_file:
                value = self.db.execute_lastrowid('INSERT INTO file SET filename = %s, file = %s, created_by = %s, created = NOW();', uploaded_file['filename'], uploaded_file['body'], self.created_by)
            field = 'value_file'
        elif definition.datatype == 'boolean':
            field = 'value_boolean'
            value = 1 if value.lower() == 'true' else 0
        elif definition.datatype == 'counter':
            field = 'value_counter'
        else:
            field = 'value_string'
            if value:
                value = value[:500]

        if property_id:
            self.db.execute('UPDATE property SET %s = %%s, changed = NOW(), changed_by = %%s WHERE id = %%s;' % field,
                value,
                self.created_by,
                property_id,
            )
        else:
            if entity_id:
                property_id = self.db.execute_lastrowid('INSERT INTO property SET entity_id = %%s, property_definition_keyname = %%s, %s = %%s, created = NOW(), created_by = %%s;' % field,
                    entity_id,
                    property_definition_keyname,
                    value,
                    self.created_by
                )
            if relationship_id:
                property_id = self.db.execute_lastrowid('INSERT INTO property SET relationship_id = %%s, property_definition_keyname = %%s, %s = %%s, created = NOW(), created_by = %%s;' % field,
                    relationship_id,
                    property_definition_keyname,
                    value,
                    self.created_by
                )

        return property_id

    def set_public(self, entity_id, is_public=False):
        """
        """
        if not entity_id:
            return

        if is_public==True:
            self.db.execute('UPDATE entity SET public = 1 WHERE id = %s', entity_id)
        else:
            self.db.execute('UPDATE entity SET public = 0 WHERE id = %s', entity_id)

    def set_counter(self, entity_id):
        """
        Sets counter property.

        """
        if not entity_id:
            return

        #Vastuskirja hack
        if self.db.get('SELECT entity_definition_keyname FROM entity WHERE id = %s', entity_id).entity_definition_keyname == 'replay':
            parent = self.get_relatives(related_entity_id=entity_id, relationship_definition_keyname='child', reverse_relation=True, limit=1).values()[0][0]
            childs = self.get_relatives(entity_id=parent.get('id',None), relationship_definition_keyname='child').values()
            if childs:
                childs_count = len([y.get('id', 0) for y in childs[0] if y.get('properties', {}).get('registry_number', {}).get('values', None)])+1
            else:
                childs_count = 1
            parent_number = ''.join(['%s' % x['value'] for x in parent.get('properties', {}).get('registry_number', {}).get('values', []) if x['value']])
            counter_value = '%s-%s' % (parent_number, childs_count)
            self.set_property(entity_id=entity_id, property_definition_keyname=287, value=counter_value)
            return counter_value


        sql ="""
            INSERT INTO property (
                entity_id,
                property_definition_keyname,
                value_string,
                created_by,
                created
            ) SELECT /* SQL_NO_CACHE */
                %(entity_id)s,
                property_definition2.keyname,
                CONCAT(
                IFNULL((
                    SELECT
                        value_string
                    FROM
                        property,
                        property_definition,
                        entity
                    WHERE property_definition.keyname = property.property_definition_keyname
                    AND entity.entity_definition_keyname = property_definition.entity_definition_keyname
                    AND entity.id = property.entity_id
                    AND property_definition.dataproperty='series'
                    AND entity.id = (SELECT entity_id FROM relationship WHERE related_entity_id = %(entity_id)s AND relationship_definition_keyname = 'child' LIMIT 1)
                    LIMIT 1
                ), ''),
                IFNULL((
                    SELECT
                        value_string
                    FROM
                        property,
                        property_definition,
                        entity
                    WHERE property_definition.keyname = property.property_definition_keyname
                    AND entity.entity_definition_keyname = property_definition.entity_definition_keyname
                    AND entity.id = property.entity_id
                    AND property_definition.dataproperty='prefix'
                    AND entity.id = (SELECT entity_id FROM relationship WHERE related_entity_id = %(entity_id)s AND relationship_definition_keyname = 'child' LIMIT 1)
                    LIMIT 1
                ), ''),
                counter.value+counter.increment) AS value,
                '%(user_id)s',
                NOW()
            FROM
                property,
                property_definition,
                relationship,
                property_definition AS property_definition2,
                counter
            WHERE property_definition.keyname = property.property_definition_keyname
            AND relationship.property_definition_keyname = property_definition.keyname
            AND property_definition2.keyname = relationship.related_property_definition_keyname
            AND counter.id = property.value_counter
            AND property.entity_id = (SELECT entity_id FROM relationship WHERE related_entity_id = %(entity_id)s AND relationship_definition_keyname = 'child' LIMIT 1)
            AND property_definition.datatype= 'counter'
            AND property_definition2.datatype = 'counter-value'
            AND relationship.relationship_definition_keyname = 'target-property'
            AND property_definition2.entity_definition_keyname = (SELECT entity_definition_keyname FROM entity WHERE id = %(entity_id)s LIMIT 1)
            AND counter.type = 'increment';
            UPDATE
            counter,
            (
                SELECT
                    counter.id
                FROM
                    property,
                    property_definition,
                    relationship,
                    property_definition AS property_definition2,
                    counter
                WHERE property_definition.keyname = property.property_definition_keyname
                AND relationship.property_definition_keyname = property_definition.keyname
                AND property_definition2.keyname = relationship.related_property_definition_keyname
                AND counter.id = property.value_counter
                AND property.entity_id = (SELECT entity_id FROM relationship WHERE related_entity_id = %(entity_id)s AND relationship_definition_keyname = 'child' LIMIT 1)
                AND property_definition.datatype= 'counter'
                AND property_definition2.datatype = 'counter-value'
                AND relationship.relationship_definition_keyname = 'target-property'
                AND property_definition2.entity_definition_keyname = (SELECT entity_definition_keyname FROM entity WHERE id = %(entity_id)s LIMIT 1)
                AND counter.type = 'increment'
                ) X
            SET
                counter.value = counter.value + counter.increment,
                counter.changed_by = '%(user_id)s',
                counter.changed = NOW()
            WHERE counter.id = X.id;
        """ % {'entity_id': entity_id, 'user_id': ','.join(map(str, self.user_id))}
        # logging.debug(sql)

        property_id = self.db.execute_lastrowid(sql)
        logging.warning(str(property_id))
        return self.db.get('SELECT value_string FROM property WHERE id = %s', property_id).value_string

    def set_relations(self, entity_id, related_entity_id, relationship_definition_keyname, delete=False, update=False):
        """
        Add or removes Entity relations. entity_id, related_entity_id, relationship_definition_keyname can be single value or list of values.

        """

        if type(entity_id) is not list:
            entity_id = [entity_id]

        if type(related_entity_id) is not list:
            related_entity_id = [related_entity_id]

        if type(relationship_definition_keyname) is not list:
            relationship_definition_keyname = [relationship_definition_keyname]

        for e in entity_id:
            for r in related_entity_id:
                for t in relationship_definition_keyname:
                    if delete == True:
                        sql = """
                            UPDATE relationship SET
                                deleted_by = '%s',
                                deleted = NOW()
                            WHERE relationship_definition_keyname = '%s'
                            AND entity_id = %s
                            AND related_entity_id = %s;
                        """ % (self.created_by, t, e, r)
                        # logging.debug(sql)
                        self.db.execute(sql)
                    elif update == True:
                        sql = """
                            UPDATE relationship SET
                                deleted_by = NULL,
                                deleted = NULL,
                                changed_by = '%s',
                                changed = NOW()
                            WHERE relationship_definition_keyname = '%s'
                            AND entity_id = %s
                            AND related_entity_id = %s;
                        """ % (self.created_by, t, e, r)
                        # logging.debug(sql)
                        old = self.db.execute_rowcount(sql)
                        if not old:
                            sql = """
                                INSERT INTO relationship SET
                                    relationship_definition_keyname = '%s',
                                    entity_id = %s,
                                    related_entity_id = %s,
                                    created_by = '%s',
                                    created = NOW();
                            """ % (t, e, r, self.created_by)
                            # logging.debug(sql)
                            self.db.execute(sql)
                    else:
                        sql = """
                            INSERT INTO relationship SET
                                relationship_definition_keyname = '%s',
                                entity_id = %s,
                                related_entity_id = %s,
                                created_by = '%s',
                                created = NOW();
                        """ % (t, e, r, self.created_by)
                        # logging.debug(sql)
                        self.db.execute(sql)

    def get(self, ids_only=False, entity_id=None, search=None, entity_definition_keyname=None, dataproperty=None, limit=None, full_definition=False, only_public=False):
        """
        If ids_only = True, then returns list of Entity IDs. Else returns list of Entities (with properties) as dictionary. entity_id, entity_definition and dataproperty can be single value or list of values. If limit = 1 returns Entity (not list). If full_definition = True returns also empty properties.

        """
        ids = self.__get_id_list(entity_id=entity_id, search=search, entity_definition_keyname=entity_definition_keyname, limit=limit, only_public=only_public)
        if ids_only == True:
            return ids

        entities = self.__get_properties(entity_id=ids, entity_definition_keyname=entity_definition_keyname, dataproperty=dataproperty, full_definition=full_definition, only_public=only_public)
        if not entities and full_definition == False and entity_definition_keyname == None:
            return

        if limit == 1:
            return entities[0]

        return entities

    def __get_id_list(self, entity_id=None, search=None, entity_definition_keyname=None, limit=None, only_public=False):
        """
        Get list of Entity IDs. entity_id, entity_definition_keyname and user_id can be single ID or list of IDs.

        """
        sql = """
            SELECT DISTINCT
                entity.id AS id
            FROM
                property_definition,
                property,
                entity,
                relationship
            WHERE property.property_definition_keyname = property_definition.keyname
            AND entity.id = property.entity_id
            AND relationship.entity_id = entity.id
        """

        if entity_id != None:
            if type(entity_id) is not list:
                entity_id = [entity_id]
            sql += ' AND entity.id IN (%s)' % ','.join(map(str, entity_id))

        if search != None:
            for s in search.split(' '):
                sql += ' AND value_string LIKE \'%%%%%s%%%%\'' % s

        if entity_definition_keyname != None:
            if type(entity_definition_keyname) is not list:
                entity_definition_keyname = [entity_definition_keyname]
            sql += ' AND entity.entity_definition_keyname IN (%s)' % ','.join(['\'%s\'' % x for x in map(str, entity_definition_keyname)])

        if self.user_id and only_public == False:
            sql += ' AND relationship.related_entity_id IN (%s) AND relationship.relationship_definition_keyname IN (\'leecher\', \'viewer\', \'editor\', \'owner\')' % ','.join(map(str, self.user_id))
        else:
            sql += ' AND entity.public = 1 AND property_definition.public = 1'

        sql += ' ORDER BY entity.sort, entity.created DESC'

        if limit != None:
            sql += ' LIMIT %d' % limit

        sql += ';'
        # logging.debug(sql)

        items = self.db.query(sql)
        if not items:
            return []
        return [x.id for x in items]

    def __get_properties(self, entity_id=None, entity_definition_keyname=None, dataproperty=None, full_definition=False, only_public=False):
        """
        Get Entity properties. entity_id can be single ID or list of IDs.

        """
        items = None
        if entity_id:
            if type(entity_id) is not list:
                entity_id = [entity_id]

            if self.user_id and only_public == False:
                public = ''
            else:
                public = 'AND entity.public = 1 AND property_definition.public = 1'

            datapropertysql = ''
            if dataproperty:
                if type(dataproperty) is not list:
                    dataproperty = [dataproperty]
                    datapropertysql = 'AND property_definition.dataproperty IN (%s)' % ','.join(['\'%s\'' % x for x in dataproperty])

            sql = """
                SELECT
                    entity_definition.keyname                       AS entity_definition_keyname,
                    entity.id                                       AS entity_id,
                    entity_definition.%(language)s_label            AS entity_label,
                    entity_definition.%(language)s_label_plural     AS entity_label_plural,
                    entity_definition.%(language)s_description      AS entity_description,
                    entity.created                                  AS entity_created,
                    entity.public                                   AS entity_public,
                    entity_definition.%(language)s_displayname      AS entity_displayname,
                    entity_definition.%(language)s_displayinfo      AS entity_displayinfo,
                    entity_definition.%(language)s_displaytable     AS entity_displaytable,
                    entity_definition.%(language)s_sort             AS entity_sort,
                    entity.sort                                     AS entity_sort_value,
                    property_definition.keyname                     AS property_keyname,
                    property_definition.ordinal                     AS property_ordinal,
                    property_definition.%(language)s_fieldset       AS property_fieldset,
                    property_definition.%(language)s_label          AS property_label,
                    property_definition.%(language)s_label_plural   AS property_label_plural,
                    property_definition.%(language)s_description    AS property_description,
                    property_definition.datatype                    AS property_datatype,
                    property_definition.dataproperty                AS property_dataproperty,
                    property_definition.multilingual                AS property_multilingual,
                    property_definition.multiplicity                AS property_multiplicity,
                    property_definition.public                      AS property_public,
                    property.id                                     AS value_id,
                    property.id                                     AS value_ordinal,
                    property.value_string                           AS value_string,
                    property.value_text                             AS value_text,
                    property.value_integer                          AS value_integer,
                    property.value_decimal                          AS value_decimal,
                    property.value_boolean                          AS value_boolean,
                    property.value_datetime                         AS value_datetime,
                    property.value_entity                           AS value_entity,
                    property.value_counter                          AS value_counter,
                    property.value_file                             AS value_file
                FROM
                    entity,
                    entity_definition,
                    property,
                    property_definition
                WHERE property.entity_id = entity.id
                AND entity_definition.keyname = entity.entity_definition_keyname
                AND property_definition.keyname = property.property_definition_keyname
                AND entity_definition.keyname = property_definition.entity_definition_keyname
                AND (property.language = '%(language)s' OR property.language IS NULL)
                AND entity.id IN (%(idlist)s)
                %(public)s
                %(datapropertysql)s
                ORDER BY
                    entity_definition.keyname,
                    entity.created DESC
            """ % {'language': self.language, 'public': public, 'idlist': ','.join(map(str, entity_id)), 'datapropertysql': datapropertysql}
            # logging.debug(sql)

            items = {}
            for row in self.db.query(sql):
                #Entity
                items.setdefault('item_%s' % row.entity_id, {})['definition_keyname'] = row.entity_definition_keyname
                items.setdefault('item_%s' % row.entity_id, {})['id'] = row.entity_id
                items.setdefault('item_%s' % row.entity_id, {})['label'] = row.entity_label
                items.setdefault('item_%s' % row.entity_id, {})['label_plural'] = row.entity_label_plural
                items.setdefault('item_%s' % row.entity_id, {})['description'] = row.entity_description
                items.setdefault('item_%s' % row.entity_id, {})['sort'] = row.entity_sort
                items.setdefault('item_%s' % row.entity_id, {})['sort_value'] = row.entity_sort_value
                items.setdefault('item_%s' % row.entity_id, {})['created'] = formatDatetime(row.entity_created, '%(day)02d.%(month)02d.%(year)d') if row.entity_created else ''
                items.setdefault('item_%s' % row.entity_id, {})['displayname'] = row.entity_displayname
                items.setdefault('item_%s' % row.entity_id, {})['displayinfo'] = row.entity_displayinfo
                items.setdefault('item_%s' % row.entity_id, {})['displaytable'] = row.entity_displaytable
                items.setdefault('item_%s' % row.entity_id, {})['file_count'] = 0
                items.setdefault('item_%s' % row.entity_id, {})['is_public'] = True if row.entity_public == 1 else False
                items.setdefault('item_%s' % row.entity_id, {})['ordinal'] = row.entity_created if row.entity_created else datetime.now()

                #Property
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['keyname'] = row.property_keyname
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['fieldset'] = row.property_fieldset
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['label'] = row.property_label
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['label_plural'] = row.property_label_plural
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['description'] = row.property_description
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['datatype'] = row.property_datatype
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['dataproperty'] = row.property_dataproperty
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['multilingual'] = row.property_multilingual
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['multiplicity'] = row.property_multiplicity
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['ordinal'] = row.property_ordinal
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['public'] = True if row.property_public == 1 else False

                #Value
                if row.property_datatype in ['string', 'select']:
                    db_value = row.value_string if row.value_string else ''
                    value = row.value_string if row.value_string else ''
                elif row.property_datatype in ['text', 'html']:
                    db_value = row.value_text if row.value_text else ''
                    value = row.value_text if row.value_text else ''
                elif row.property_datatype == 'integer':
                    db_value = row.value_integer
                    value = row.value_integer
                elif row.property_datatype == 'decimal':
                    db_value = row.value_decimal
                    value = row.value_decimal
                elif row.property_datatype == 'date':
                    db_value = row.value_datetime
                    value = formatDatetime(row.value_datetime, '%(day)02d.%(month)02d.%(year)d')
                elif row.property_datatype == 'datetime':
                    db_value = row.value_datetime
                    value = formatDatetime(row.value_datetime)
                elif row.property_datatype == 'reference':
                    db_value = row.value_entity
                    value = row.value_entity
                elif row.property_datatype == 'file':
                    db_value = row.value_file
                    blobstore = self.db.get('SELECT id, filename, filesize FROM file WHERE id=%s LIMIT 1', row.value_file)
                    value = blobstore.filename if blobstore else ''
                    items.setdefault('item_%s' % row.entity_id, {})['file_count'] += 1
                elif row.property_datatype == 'boolean':
                    db_value = row.value_boolean
                    value = self.user_locale.translate('boolean_true') if row.value_boolean == 1 else self.user_locale.translate('boolean_false')
                elif row.property_datatype == 'counter':
                    counter = self.db.get('SELECT %(language)s_label AS label FROM counter WHERE id=%(id)s LIMIT 1' % {'language': self.language, 'id': row.value_counter})
                    db_value = row.value_counter
                    value = counter.label
                elif row.property_datatype == 'counter-value':
                    db_value = row.value_string
                    value = row.value_string
                else:
                    db_value = ''
                    value = 'X'

                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {}).setdefault('values', {}).setdefault('value_%s' % row.value_id, {})['id'] = row.value_id
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {}).setdefault('values', {}).setdefault('value_%s' % row.value_id, {})['ordinal'] = row.value_ordinal
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {}).setdefault('values', {}).setdefault('value_%s' % row.value_id, {})['value'] = value
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {}).setdefault('values', {}).setdefault('value_%s' % row.value_id, {})['db_value'] = db_value

        if not items:
            if not full_definition:
                return []

            if entity_definition_keyname:
                if type(entity_definition_keyname) is not list:
                    entity_definition_keyname = [entity_definition_keyname]

                items = {}
                for e in entity_definition_keyname:
                    items.setdefault('item_%s' % e, {})['definition_keyname'] = e
                    items.setdefault('item_%s' % e, {})['ordinal'] = 'X'

        for key, value in items.iteritems():
            if value.get('id', None):
                items[key] = dict(items[key].items() + self.__get_displayfields(value).items())
                items[key]['displaypicture'] = self.__get_picture_url(value['id'])

            if full_definition:
                for d in self.get_definition(entity_definition_keyname=value['definition_keyname']):
                    if not value.get('id', None):
                        items[key]['displayname'] = d.entity_label
                    items[key].setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['keyname'] = d.property_keyname
                    items[key].setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['fieldset'] = d.property_fieldset
                    items[key].setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['label'] = d.property_label
                    items[key].setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['label_plural'] = d.property_label_plural
                    items[key].setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['description'] = d.property_description
                    items[key].setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['datatype'] = d.property_datatype
                    items[key].setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['dataproperty'] = d.property_dataproperty
                    items[key].setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['multilingual'] = d.property_multilingual
                    items[key].setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['multiplicity'] = d.property_multiplicity
                    items[key].setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['ordinal'] = d.property_ordinal
                    items[key].setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['public'] = d.property_public
                    if not d.property_multiplicity or d.property_multiplicity > len(value.get('properties', {}).get('%s' % d.property_dataproperty, {}).get('values', {}).values()):
                        items[key].setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {}).setdefault('values', {})['value_new'] = {'id': '', 'ordinal': 'X', 'value': '', 'db_value': ''}
                    if not d.property_multiplicity or d.property_multiplicity > len(value.get('properties', {}).get('%s' % d.property_dataproperty, {}).get('values', {}).values()):
                        items[key].setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['can_add_new'] = True
                    else:
                        items[key].setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['can_add_new'] = False

                    if d.property_classifier_id:
                        for c in self.get(entity_definition_keyname=d.property_classifier_id, only_public=True):
                            if c.get('id', None):
                                items[key].setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {}).setdefault('select', []).append({'id': c.get('id', ''), 'label': c.get('displayname', '')})

            for p_key, p_value in value.get('properties', {}).iteritems():
                if p_value.get('select', None):
                    items[key]['properties'][p_key]['select'] = sorted(p_value['select'], key=itemgetter('label'))
                items[key]['properties'][p_key]['values'] = sorted(p_value.get('values', {}).values(), key=itemgetter('ordinal'))

        return items.values()

    def __get_displayfields(self, entity_dict):
        """
        Returns Entity displayname, displayinfo, displaytable fields.

        """
        result = {}
        for displayfield in ['displayname', 'displayinfo', 'displaytable', 'sort']:
            result[displayfield] = entity_dict.get(displayfield, '') if entity_dict.get(displayfield, '') else ''
            for data_property in findTags(entity_dict.get(displayfield, ''), '@', '@'):
                result[displayfield] = result[displayfield].replace('@%s@' % data_property, ', '.join(['%s' % x['value'] for x in entity_dict.get('properties', {}).get(data_property, {}).get('values', {}).values()]))

        result['displaytable_labels'] = entity_dict.get('displaytable', '') if entity_dict.get('displaytable', '') else ''
        for data_property in findTags(entity_dict.get('displaytable', ''), '@', '@'):
            result['displaytable_labels'] = result['displaytable_labels'].replace('@%s@' % data_property, entity_dict.get('properties', {}).get(data_property, {}).get('label', ''))

        result['displaytable'] = result['displaytable'].split('|') if result['displaytable'] else None
        result['displaytable_labels'] = result['displaytable_labels'].split('|') if result['displaytable_labels'] else None

        if entity_dict.get('id', None) and entity_dict.get('sort_value', None) != result['sort']:
            self.db.execute('UPDATE entity SET sort = %s WHERE id = %s', result['sort'], entity_dict.get('id'))

        return result

    def __get_picture_url(self, entity_id):
        """
        Returns Entity picture.

        """
        sql = """
            SELECT
                file.id
            FROM
                property,
                property_definition,
                file
            WHERE property_definition.keyname=property.property_definition_keyname
            AND file.id = property.value_file
            AND property_definition.dataproperty='photo'
            AND property.entity_id=%s
            LIMIT 1;
        """
        f = self.db.get(sql, entity_id)
        if not f:
            return 'https://secure.gravatar.com/avatar/%s?d=identicon&s=150' % (hashlib.md5(str(entity_id)).hexdigest())

        return '/entity/file-%s' % f.id

    def get_definition(self, entity_definition_keyname):
        """
        Returns Entity definition.

        """
        if not entity_definition_keyname:
            return

        if type(entity_definition_keyname) is not list:
            entity_definition_keyname = [entity_definition_keyname]

        sql = """
            SELECT
                entity_definition.keyname AS entity_definition_keyname,
                entity_definition.%(language)s_label AS entity_label,
                entity_definition.%(language)s_label_plural AS entity_label_plural,
                entity_definition.%(language)s_description AS entity_description,
                entity_definition.%(language)s_displayname AS entity_displayname,
                entity_definition.%(language)s_displayinfo AS entity_displayinfo,
                entity_definition.%(language)s_displaytable AS entity_displaytable,
                property_definition.keyname AS property_keyname,
                property_definition.%(language)s_fieldset AS property_fieldset,
                property_definition.%(language)s_label AS property_label,
                property_definition.%(language)s_label_plural AS property_label_plural,
                property_definition.%(language)s_description AS property_description,
                property_definition.datatype AS property_datatype,
                property_definition.dataproperty AS property_dataproperty,
                property_definition.multilingual AS property_multilingual,
                property_definition.multiplicity AS property_multiplicity,
                property_definition.ordinal AS property_ordinal,
                property_definition.public AS property_public,
                property_definition.classifying_entity_definition_keyname AS property_classifier_id
            FROM
                entity_definition,
                property_definition
            WHERE entity_definition.keyname = property_definition.entity_definition_keyname
            AND entity_definition.keyname IN (%(keyname)s)
        """ % {'language': self.language, 'keyname': ','.join(['\'%s\'' % x for x in map(str, entity_definition_keyname)])}
        # logging.debug(sql)

        return self.db.query(sql)

    def get_relatives(self, ids_only=False, relationship_ids_only=False, entity_id=None, related_entity_id=None, relationship_definition_keyname=None, reverse_relation=False, entity_definition_keyname=None, full_definition=False, limit=None, only_public=False):
        """
        Get Entity relatives.

        """
        if entity_id:
            if type(entity_id) is not list:
                entity_id = [entity_id]

        if related_entity_id:
            if type(related_entity_id) is not list:
                related_entity_id = [related_entity_id]

        if relationship_definition_keyname:
            if type(relationship_definition_keyname) is not list:
                relationship_definition_keyname = [relationship_definition_keyname]

        if entity_definition_keyname:
            if type(entity_definition_keyname) is not list:
                entity_definition_keyname = [entity_definition_keyname]

        if reverse_relation == True:
            sql = """
                SELECT DISTINCT
                    relationship.id AS relationship_id,
                    relationship.relationship_definition_keyname,
                    relationship.entity_id AS id
                FROM
                    entity,
                    relationship,
                    relationship AS rights
                WHERE relationship.entity_id = entity.id
                AND rights.entity_id = entity.id
                AND relationship.deleted IS NULL
            """
        else:
            sql = """
                SELECT DISTINCT
                    relationship.id AS relationship_id,
                    relationship.relationship_definition_keyname,
                    relationship.related_entity_id AS id
                FROM
                    entity,
                    relationship,
                    relationship AS rights
                WHERE relationship.related_entity_id = entity.id
                AND rights.entity_id = entity.id
                AND relationship.deleted IS NULL
            """
        if entity_id:
            sql += ' AND relationship.entity_id IN (%s)' % ','.join(map(str, entity_id))

        if related_entity_id:
            sql += ' AND relationship.related_entity_id IN (%s)' % ','.join(map(str, related_entity_id))

        if self.user_id and only_public == False:
            sql += ' AND rights.related_entity_id IN (%s) AND rights.relationship_definition_keyname IN (\'leecher\', \'viewer\', \'editor\', \'owner\')' % ','.join(map(str, self.user_id))
        else:
            sql += ' AND entity.public = 1'

        if relationship_definition_keyname:
            sql += ' AND relationship.relationship_definition_keyname IN (%s)' % ','.join(['\'%s\'' % x for x in relationship_definition_keyname])

        if entity_definition_keyname:
            sql += ' AND entity.entity_definition_keyname IN (%s)' % ','.join(map(str, entity_definition_keyname))

        sql += ' ORDER BY entity.id DESC'

        if limit:
            sql += ' LIMIT %d' % limit

        sql += ';'
        # logging.debug(sql)

        if ids_only == True:
            items = []
            for item in self.db.query(sql):
                items.append(item.id)
        elif relationship_ids_only == True:
            items = []
            for item in self.db.query(sql):
                items.append(item.relationship_id)
        else:
            items = {}
            for item in self.db.query(sql):
                ent = self.__get_properties(entity_id=item.id, full_definition=full_definition, entity_definition_keyname=entity_definition_keyname, only_public=only_public)
                if not ent:
                    continue
                ent = ent[0]
                items.setdefault('%s' % ent.get('label_plural', ''), []).append(ent)

                for k, v in items.iteritems():
                    items[k] = sorted(v, key=itemgetter('ordinal'), reverse=True)

        return items

    def get_file(self, file_id):
        """
        Returns file object. File properties are id, file, filename.

        """

        if self.user_id:
            public = ''
        else:
            public = 'AND property_definition.public = 1'

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
            AND property_definition.keyname = property.property_definition_keyname
            AND file.id = %(file_id)s
            %(public)s
            LIMIT 1
            """ % {'file_id': file_id, 'public': public}
        # logging.debug(sql)

        result = self.db.get(sql)

        if not result:
            return
        if not result.file:
            return

        return result

    def get_entity_definition(self, entity_definition_keyname):
        """
        Returns entity_definition.

        """
        if entity_definition_keyname:
            if type(entity_definition_keyname) is not list:
                entity_definition_keyname = [entity_definition_keyname]

        sql = """
            SELECT
                keyname,
                %(language)s_label AS label,
                %(language)s_label_plural AS label_plural,
                %(language)s_description AS description,
                %(language)s_menu AS menugroup,
                ordinal,
                actions_add
            FROM
                entity_definition
            WHERE keyname IN (%(ids)s);
        """  % {'language': self.language, 'ids': ','.join(['\'%s\'' % x for x in map(str, entity_definition_keyname)])}
        # logging.debug(sql)

        return self.db.query(sql)

    def get_allowed_childs(self, entity_id):
        """
        Returns allowed child definitions.

        """
        sql = """
            SELECT DISTINCT
                entity_definition.keyname,
                entity_definition.%(language)s_label AS label,
                entity_definition.%(language)s_label_plural AS label_plural,
                entity_definition.%(language)s_description AS description,
                entity_definition.%(language)s_menu AS menugroup
            FROM
                entity_definition,
                relationship
            WHERE relationship.related_entity_definition_keyname = entity_definition.keyname
            AND relationship.relationship_definition_keyname = 'allowed-child'
            AND relationship.entity_id = %(id)s
        """  % {'language': self.language, 'id': entity_id}
        # logging.debug(sql)

        result = self.db.query(sql)
        if result:
            return result

        sql = """
            SELECT DISTINCT
                entity_definition.keyname,
                entity_definition.%(language)s_label AS label,
                entity_definition.%(language)s_label_plural AS label_plural,
                entity_definition.%(language)s_description AS description,
                entity_definition.%(language)s_menu AS menugroup
            FROM
                entity_definition,
                relationship
            WHERE relationship.related_entity_definition_keyname = entity_definition.keyname
            AND relationship.relationship_definition_keyname = 'allowed-child'
            AND relationship.entity_definition_keyname = (SELECT entity_definition_keyname FROM entity WHERE id = %(id)s)
        """  % {'language': self.language, 'id': entity_id}
        # logging.debug(sql)

        return self.db.query(sql)

    def get_menu(self):
        """
        Returns user menu.

        """

        sql = """
            SELECT DISTINCT
                entity_definition.keyname,
                entity_definition.%(language)s_menu AS menugroup,
                entity_definition.%(language)s_label AS item
            FROM
                entity_definition,
                entity,
                relationship
            WHERE entity.entity_definition_keyname = entity_definition.keyname
            AND relationship.entity_id = entity.id
            AND relationship.relationship_definition_keyname IN ('viewer', 'editor', 'owner')
            AND entity_definition.estonian_menu IS NOT NULL
            AND relationship.related_entity_id IN (%(user_id)s)
            ORDER BY
            entity_definition.estonian_menu,
            entity_definition.estonian_label;
        """ % {'language': self.language, 'user_id': ','.join(map(str, self.user_id))}
        # logging.debug(sql)

        menu = {}
        for m in self.db.query(sql):
            menu.setdefault(m.menugroup, {})['label'] = m.menugroup
            menu.setdefault(m.menugroup, {}).setdefault('items', []).append({'keyname': m.keyname, 'title': m.item})

        return sorted(menu.values(), key=itemgetter('label'))


class User():
    """
    If session is given returns user object. User properties are id, name, email, picture, language.

    """
    id          = None
    name        = None
    email       = None
    picture     = None
    language    = None

    def __init__(self, session=None):
        if not session:
            return

        db = connection()
        user = db.get("""
            SELECT
                property.entity_id AS id,
                user.name,
                user.language,
                user.email,
                user.picture,
                user_profile.provider
            FROM
                property_definition,
                property,
                user,
                user_profile
            WHERE property.property_definition_keyname = property_definition.keyname
            AND user.email = property.value_string
            AND user_profile.user_id = user.id
            AND property_definition.dataproperty = 'user'
            AND user_profile.session = %s
            LIMIT 1;
        """, session)

        if not user:
            return

        for k, v in user.items():
            setattr(self, k, v)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def create(self, provider='', id='', email='', name='', picture='', language='', session=''):
        """
        Creates new (or updates old) user.

        """
        db = connection()
        profile_id = db.execute_lastrowid('INSERT INTO user_profile SET provider = %s, provider_id = %s, email = %s, name = %s, picture = %s, session = %s, created = NOW() ON DUPLICATE KEY UPDATE email = %s, name = %s, picture = %s, session = %s, changed = NOW();',
                provider,
                id,
                email,
                name,
                picture,
                session,
                email,
                name,
                picture,
                session
            )
        profile = db.get('SELECT id, user_id FROM user_profile WHERE id = %s', profile_id)

        if not profile.user_id:
            user_id = db.execute_lastrowid('INSERT INTO user SET email = %s, name = %s, picture = %s, language = %s, created = NOW();',
                email,
                name,
                picture,
                language
            )
            db.execute('UPDATE user_profile SET user_id = %s WHERE id = %s;', user_id, profile.id)


def formatDatetime(date, format='%(day)02d.%(month)02d.%(year)d %(hour)02d:%(minute)02d'):
    """
    Formats and returns date as string. Format tags are %(day)02d, %(month)02d, %(year)d, %(hour)02d and %(minute)02d.

    """
    if not date:
        return ''
    return format % {'year': date.year, 'month': date.month, 'day': date.day, 'hour': date.hour, 'minute': date.minute}


def findTags(s, beginning, end):
    """
    Finds and returns list of tags from string.

    """
    if not s:
        return []
    return re.compile('%s(.*?)%s' % (beginning, end), re.DOTALL).findall(s)
