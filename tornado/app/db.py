from tornado import database
from tornado import locale
from tornado.options import options

from operator import itemgetter

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

    def create(self, entity_definition_id, parent_entity_id=None):
        """
        Creates new Entity and returns its ID.

        """
        if not entity_definition_id:
            return

        # Create entity
        sql = """
            INSERT INTO entity SET
                entity_definition_id = %s,
                created_by = %s,
                created = NOW();
        """
        # logging.debug(sql)
        entity_id = self.db.execute_lastrowid(sql, entity_definition_id, self.created_by)

        if not parent_entity_id:
            return entity_id

        # Insert child relationship
        sql = """
            INSERT INTO relationship SET
                relationship_definition_id = (SELECT id FROM relationship_definition WHERE type = 'child' LIMIT 1),
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
                relationship_definition_id,
                entity_id,
                related_entity_id,
                created_by,
                created
            ) SELECT /* SQL_NO_CACHE */
                relationship.relationship_definition_id,
                %s,
                relationship.related_entity_id,
                %s,
                NOW()
            FROM
                relationship,
                relationship_definition
            WHERE relationship_definition.id = relationship.relationship_definition_id
            AND relationship_definition.type IN ('leecher', 'viewer', 'editor', 'owner')
            AND relationship.entity_id = %s;
        """
        # logging.debug(sql)
        self.db.execute(sql, entity_id, self.created_by, parent_entity_id)

        # Propagate properties
        sql = """
            INSERT INTO property (
                entity_id,
                property_definition_id,
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
                relationship.related_property_definition_id,
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
                property,
                relationship_definition
            WHERE property_definition.id = relationship.property_definition_id
            AND property.property_definition_id = property_definition.id
            AND relationship_definition.id = relationship.relationship_definition_id
            AND property_definition.entity_definition_id = %s
            AND property.entity_id = %s
            AND relationship_definition.type = 'propagated_property';
        """
        # logging.debug(sql)
        self.db.execute(sql, entity_id, self.created_by, entity_definition_id, parent_entity_id)

        return entity_id

    def set_property(self, entity_id=None, relationship_id=None, property_definition_id=None, value=None, property_id=None, uploaded_file=None):
        """
        Saves property value. Creates new one if property_id = None. Returns property ID.

        """
        if not entity_id and not relationship_id:
            return

        if not property_definition_id:
            return

        if relationship_id:
            logging.debug(relationship_id)

        definition = self.db.get('SELECT datatype FROM property_definition WHERE id = %s LIMIT 1;', property_definition_id)
        if definition.datatype == 'text':
            field = 'value_text'
        elif definition.datatype == 'integer':
            field = 'value_integer'
        elif definition.datatype == 'float':
            field = 'value_decimal'
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
                property_id = self.db.execute_lastrowid('INSERT INTO property SET entity_id = %%s, property_definition_id = %%s, %s = %%s, created = NOW(), created_by = %%s;' % field,
                    entity_id,
                    property_definition_id,
                    value,
                    self.created_by
                )
            if relationship_id:
                property_id = self.db.execute_lastrowid('INSERT INTO property SET relationship_id = %%s, property_definition_id = %%s, %s = %%s, created = NOW(), created_by = %%s;' % field,
                    relationship_id,
                    property_definition_id,
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
        if self.db.get('SELECT entity_definition_id FROM entity WHERE id = %s', entity_id).entity_definition_id == 38:
            parent = self.get_relatives(entity_id=entity_id, relation_type='child', reverse_relation=True, limit=1).values()[0][0]
            childs = self.get_relatives(entity_id=parent.get('id',None), relation_type='child').values()
            if childs:
                childs_count = len([y.get('id', 0) for y in childs[0] if y.get('properties', {}).get('registry_number', {}).get('values', None)])+1
            else:
                childs_count = 1
            parent_number = ''.join(['%s' % x['value'] for x in parent.get('properties', {}).get('registry_number', {}).get('values', []) if x['value']])
            counter_value = '%s-%s' % (parent_number, childs_count)
            self.set_property(entity_id=entity_id, property_definition_id=287, value=counter_value)
            return counter_value


        sql ="""
            INSERT INTO property (
                entity_id,
                property_definition_id,
                value_string,
                created_by,
                created
            ) SELECT /* SQL_NO_CACHE */
                %(entity_id)s,
                property_definition2.id,
                CONCAT(
                IFNULL((
                    SELECT
                        value_string
                    FROM
                        property,
                        property_definition,
                        entity
                    WHERE property_definition.id = property.property_definition_id
                    AND entity.entity_definition_id = property_definition.entity_definition_id
                    AND entity.id = property.entity_id
                    AND property_definition.dataproperty='series'
                    AND entity.id = (SELECT entity_id FROM relationship, relationship_definition WHERE relationship_definition.id = relationship.relationship_definition_id AND related_entity_id = %(entity_id)s AND relationship_definition.type = 'child' LIMIT 1)
                    LIMIT 1
                ), ''),
                IFNULL((
                    SELECT
                        value_string
                    FROM
                        property,
                        property_definition,
                        entity
                    WHERE property_definition.id = property.property_definition_id
                    AND entity.entity_definition_id = property_definition.entity_definition_id
                    AND entity.id = property.entity_id
                    AND property_definition.dataproperty='prefix'
                    AND entity.id = (SELECT entity_id FROM relationship, relationship_definition WHERE relationship_definition.id = relationship.relationship_definition_id AND related_entity_id = %(entity_id)s AND relationship_definition.type = 'child' LIMIT 1)
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
            WHERE property_definition.id = property.property_definition_id
            AND relationship.property_definition_id = property_definition.id
            AND property_definition2.id = relationship.related_property_definition_id
            AND counter.id = property.value_counter
            AND property.entity_id = (SELECT entity_id FROM relationship, relationship_definition WHERE relationship_definition.id = relationship.relationship_definition_id AND related_entity_id = %(entity_id)s AND relationship_definition.type = 'child' LIMIT 1)
            AND property_definition.datatype= 'counter'
            AND property_definition2.datatype = 'counter_value'
            AND relationship.relationship_definition_id = (SELECT id FROM relationship_definition WHERE type = 'target_property' LIMIT 1)
            AND property_definition2.entity_definition_id = (SELECT entity_definition_id FROM entity WHERE id = %(entity_id)s LIMIT 1)
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
                WHERE property_definition.id = property.property_definition_id
                AND relationship.property_definition_id = property_definition.id
                AND property_definition2.id = relationship.related_property_definition_id
                AND counter.id = property.value_counter
                AND property.entity_id = (SELECT entity_id FROM relationship, relationship_definition WHERE relationship_definition.id = relationship.relationship_definition_id AND related_entity_id = %(entity_id)s AND relationship_definition.type = 'child' LIMIT 1)
                AND property_definition.datatype= 'counter'
                AND property_definition2.datatype = 'counter_value'
                AND relationship.relationship_definition_id = (SELECT id FROM relationship_definition WHERE type = 'target_property' LIMIT 1)
                AND property_definition2.entity_definition_id = (SELECT entity_definition_id FROM entity WHERE id = %(entity_id)s LIMIT 1)
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
        return self.db.get('SELECT value_string FROM property WHERE id=%s', property_id).value_string

    def set_relations(self, entity_id, related_entity_id, relationship_type, delete=False, update=False):
        """
        Add or removes Entity relations. entity_id, related_entity_id, relationship_type can be single value or list of values.

        """

        if type(entity_id) is not list:
            entity_id = [entity_id]

        if type(related_entity_id) is not list:
            related_entity_id = [related_entity_id]

        if type(relationship_type) is not list:
            relationship_type = [relationship_type]

        for e in entity_id:
            for r in related_entity_id:
                for t in relationship_type:
                    if delete == True:
                        sql = """
                            UPDATE relationship SET
                                deleted_by = '%s',
                                deleted = NOW()
                            WHERE relationship_definition_id = (SELECT id FROM relationship_definition WHERE type = '%s' LIMIT 1)
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
                            WHERE relationship_definition_id = (SELECT id FROM relationship_definition WHERE type = '%s' LIMIT 1)
                            AND entity_id = %s
                            AND related_entity_id = %s;
                        """ % (self.created_by, t, e, r)
                        # logging.debug(sql)
                        old = self.db.execute_rowcount(sql)
                        if not old:
                            sql = """
                                INSERT INTO relationship SET
                                    relationship_definition_id = (SELECT id FROM relationship_definition WHERE type = '%s' LIMIT 1),
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
                                relationship_definition_id = (SELECT id FROM relationship_definition WHERE type = '%s' LIMIT 1),
                                entity_id = %s,
                                related_entity_id = %s,
                                created_by = '%s',
                                created = NOW();
                        """ % (t, e, r, self.created_by)
                        # logging.debug(sql)
                        self.db.execute(sql)

    def get(self, ids_only=False, entity_id=None, search=None, entity_definition_id=None, dataproperty=None, limit=None, full_definition=False, only_public=False):
        """
        If ids_only = True, then returns list of Entity IDs. Else returns list of Entities (with properties) as dictionary. entity_id, entity_definition and dataproperty can be single value or list of values. If limit = 1 returns Entity (not list). If full_definition = True returns also empty properties.

        """
        ids = self.__get_id_list(entity_id=entity_id, search=search, entity_definition_id=entity_definition_id, limit=limit, only_public=only_public)
        if ids_only == True:
            return ids

        entities = self.__get_properties(entity_id=ids, entity_definition_id=entity_definition_id, dataproperty=dataproperty, full_definition=full_definition, only_public=only_public)
        if not entities and full_definition == False and entity_definition_id == None:
            return

        if limit == 1:
            return entities[0]

        return entities

    def __get_id_list(self, entity_id=None, search=None, entity_definition_id=None, limit=None, only_public=False):
        """
        Get list of Entity IDs. entity_id, entity_definition_id and user_id can be single ID or list of IDs.

        """
        sql = """
            SELECT DISTINCT
                entity.id AS id
            FROM
                property_definition,
                property,
                entity,
                relationship,
                relationship_definition
            WHERE property.property_definition_id = property_definition.id
            AND entity.id = property.entity_id
            AND relationship.entity_id = entity.id
            AND relationship_definition.id = relationship.relationship_definition_id
        """

        if entity_id != None:
            if type(entity_id) is not list:
                entity_id = [entity_id]
            sql += ' AND entity.id IN (%s)' % ','.join(map(str, entity_id))

        if search != None:
            for s in search.split(' '):
                sql += ' AND value_string LIKE \'%%%%%s%%%%\'' % s

        if entity_definition_id != None:
            if type(entity_definition_id) is not list:
                entity_definition_id = [entity_definition_id]
            sql += ' AND entity.entity_definition_id IN (%s)' % ','.join(map(str, entity_definition_id))

        if self.user_id and only_public == False:
            sql += ' AND relationship.related_entity_id IN (%s) AND relationship_definition.type IN (\'leecher\', \'viewer\', \'editor\', \'owner\')' % ','.join(map(str, self.user_id))
        else:
            sql += ' AND entity.public = 1 AND property_definition.public = 1'

        sql += ' ORDER BY entity.created DESC'

        if limit != None:
            sql += ' LIMIT %d' % limit

        sql += ';'
        # logging.debug(sql)

        items = self.db.query(sql)
        if not items:
            return []
        return [x.id for x in items]

    def __get_properties(self, entity_id=None, entity_definition_id=None, dataproperty=None, full_definition=False, only_public=False):
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
                    entity_definition.id                            AS entity_definition_id,
                    entity.gae_key                                  AS entity_gaekey,
                    entity.id                                       AS entity_id,
                    entity_definition.%(language)s_label            AS entity_label,
                    entity_definition.%(language)s_label_plural     AS entity_label_plural,
                    entity_definition.%(language)s_description      AS entity_description,
                    entity.created                                  AS entity_created,
                    entity.public                                   AS entity_public,
                    entity_definition.%(language)s_displayname      AS entity_displayname,
                    entity_definition.%(language)s_displayinfo      AS entity_displayinfo,
                    entity_definition.%(language)s_displaytable     AS entity_displaytable,
                    property_definition.id                          AS property_id,
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
                AND entity_definition.id = entity.entity_definition_id
                AND property_definition.id = property.property_definition_id
                AND entity_definition.id = property_definition.entity_definition_id
                AND (property.language = '%(language)s' OR property.language IS NULL)
                AND entity.id IN (%(idlist)s)
                %(public)s
                %(datapropertysql)s
                ORDER BY
                    entity_definition.id,
                    entity.created DESC
            """ % {'language': self.language, 'public': public, 'idlist': ','.join(map(str, entity_id)), 'datapropertysql': datapropertysql}
            # logging.debug(sql)

            items = {}
            for row in self.db.query(sql):
                #Entity
                items.setdefault('item_%s' % row.entity_id, {})['definition_id'] = row.entity_definition_id
                items.setdefault('item_%s' % row.entity_id, {})['id'] = row.entity_id
                items.setdefault('item_%s' % row.entity_id, {})['gae_key'] = row.entity_gaekey
                items.setdefault('item_%s' % row.entity_id, {})['label'] = row.entity_label
                items.setdefault('item_%s' % row.entity_id, {})['label_plural'] = row.entity_label_plural
                items.setdefault('item_%s' % row.entity_id, {})['description'] = row.entity_description
                items.setdefault('item_%s' % row.entity_id, {})['created'] = formatDatetime(row.entity_created, '%(day)02d.%(month)02d.%(year)d') if row.entity_created else ''
                items.setdefault('item_%s' % row.entity_id, {})['displayname'] = row.entity_displayname
                items.setdefault('item_%s' % row.entity_id, {})['displayinfo'] = row.entity_displayinfo
                items.setdefault('item_%s' % row.entity_id, {})['displaytable'] = row.entity_displaytable
                items.setdefault('item_%s' % row.entity_id, {})['file_count'] = 0
                items.setdefault('item_%s' % row.entity_id, {})['is_public'] = True if row.entity_public == 1 else False
                items.setdefault('item_%s' % row.entity_id, {})['ordinal'] = row.entity_created

                #Property
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['id'] = row.property_id
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['fieldset'] = row.property_fieldset
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['label'] = row.property_label
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['label_plural'] = row.property_label_plural
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['description'] = row.property_description
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['datatype'] = row.property_datatype
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['dataproperty'] = row.property_dataproperty
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['multilingual'] = row.property_multilingual
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['multiplicity'] = row.property_multiplicity
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['ordinal'] = row.property_ordinal
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['public'] = True if row.property_public else False

                #Value
                if row.property_datatype in ['string', 'select']:
                    db_value = row.value_string if row.value_string else ''
                    value = row.value_string if row.value_string else ''
                elif row.property_datatype == 'text':
                    db_value = row.value_text if row.value_text else ''
                    value = row.value_text if row.value_text else ''
                elif row.property_datatype == 'integer':
                    db_value = row.value_integer
                    value = row.value_integer
                elif row.property_datatype == 'float':
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
                    value = blobstore.filename
                    items.setdefault('item_%s' % row.entity_id, {})['file_count'] += 1
                elif row.property_datatype == 'boolean':
                    db_value = row.value_boolean
                    value = self.user_locale.translate('boolean_true') if row.value_boolean == 1 else self.user_locale.translate('boolean_false')
                elif row.property_datatype == 'counter':
                    counter = self.db.get('SELECT %(language)s_label AS label FROM counter WHERE id=%(id)s LIMIT 1' % {'language': self.language, 'id': row.value_counter})
                    db_value = row.value_counter
                    value = counter.label
                elif row.property_datatype == 'counter_value':
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

            if entity_definition_id:
                if type(entity_definition_id) is not list:
                    entity_definition_id = [entity_definition_id]

                items = {}
                for e in entity_definition_id:
                    items.setdefault('item_%s' % entity_definition_id, {})['definition_id'] = entity_definition_id
                    items.setdefault('item_%s' % entity_definition_id, {})['ordinal'] = 'X'

        for key, value in items.iteritems():
            if value.get('id', None):
                items[key] = dict(items[key].items() + self.__get_displayfields(value).items())
                items[key]['displaypicture'] = self.__get_picture_url(value['id'])

            if full_definition:
                for d in self.get_definition(entity_definition_id=value['definition_id']):
                    if not value.get('id', None):
                        items[key]['displayname'] = self.user_locale.translate('new_entity_label') % d.entity_label
                    items[key].setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['id'] = d.property_id
                    items[key].setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['fieldset'] = d.property_fieldset
                    items[key].setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['label'] = d.property_label
                    items[key].setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['label_plural'] = d.property_label_plural
                    items[key].setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['description'] = d.property_description
                    items[key].setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['datatype'] = d.property_datatype
                    items[key].setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['dataproperty'] = d.property_dataproperty
                    items[key].setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['multilingual'] = d.property_multilingual
                    items[key].setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['multiplicity'] = d.property_multiplicity
                    items[key].setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['ordinal'] = d.property_ordinal
                    if not d.property_multiplicity or d.property_multiplicity > len(value.get('properties', {}).get('%s' % d.property_dataproperty, {}).get('values', {}).values()):
                        items[key].setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {}).setdefault('values', {})['value_new'] = {'id': '', 'ordinal': 'X', 'value': '', 'db_value': ''}
                    if not d.property_multiplicity or d.property_multiplicity > len(value.get('properties', {}).get('%s' % d.property_dataproperty, {}).get('values', {}).values()):
                        items[key].setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['can_add_new'] = True
                    else:
                        items[key].setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['can_add_new'] = False

                    if d.property_classifier_id:
                        for c in self.get(entity_definition_id=d.property_classifier_id, only_public=True):
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
        for displayfield in ['displayname', 'displayinfo', 'displaytable']:
            result[displayfield] = entity_dict.get(displayfield, '') if entity_dict.get(displayfield, '') else ''
            for data_property in findTags(entity_dict.get(displayfield, ''), '@', '@'):
                result[displayfield] = result[displayfield].replace('@%s@' % data_property, ', '.join(['%s' % x['value'] for x in entity_dict.get('properties', {}).get(data_property, {}).get('values', {}).values()]))

        result['displaytable_labels'] = entity_dict.get('displaytable', '') if entity_dict.get('displaytable', '') else ''
        for data_property in findTags(entity_dict.get('displaytable', ''), '@', '@'):
            result['displaytable_labels'] = result['displaytable_labels'].replace('@%s@' % data_property, entity_dict.get('properties', {}).get(data_property, {}).get('label', ''))

        result['displaytable'] = result['displaytable'].split('|') if result['displaytable'] else None
        result['displaytable_labels'] = result['displaytable_labels'].split('|') if result['displaytable_labels'] else None

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
            WHERE property_definition.id=property.property_definition_id
            AND file.id = property.value_file
            AND property_definition.dataproperty='photo'
            AND property.entity_id=%s
            LIMIT 1;
        """
        f = self.db.get(sql, entity_id)
        if not f:
            return 'http://www.gravatar.com/avatar/%s?d=identicon&s=150' % (hashlib.md5(str(entity_id)).hexdigest())

        return '/entity/file-%s' % f.id

    def get_definition(self, entity_definition_id):
        """
        Returns Entity definition.

        """
        if not entity_definition_id:
            return

        if type(entity_definition_id) is not list:
            entity_definition_id = [entity_definition_id]

        sql = """
            SELECT
                entity_definition.id AS entity_definition_id,
                entity_definition.%(language)s_label AS entity_label,
                entity_definition.%(language)s_label_plural AS entity_label_plural,
                entity_definition.%(language)s_description AS entity_description,
                entity_definition.%(language)s_displayname AS entity_displayname,
                entity_definition.%(language)s_displayinfo AS entity_displayinfo,
                entity_definition.%(language)s_displaytable AS entity_displaytable,
                property_definition.id AS property_id,
                property_definition.%(language)s_fieldset AS property_fieldset,
                property_definition.%(language)s_label AS property_label,
                property_definition.%(language)s_label_plural AS property_label_plural,
                property_definition.%(language)s_description AS property_description,
                property_definition.datatype AS property_datatype,
                property_definition.dataproperty AS property_dataproperty,
                property_definition.multilingual AS property_multilingual,
                property_definition.multiplicity AS property_multiplicity,
                property_definition.ordinal AS property_ordinal,
                property_definition.classifying_entity_definition_id AS property_classifier_id
            FROM
                entity_definition,
                property_definition
            WHERE entity_definition.id = property_definition.entity_definition_id
            AND entity_definition.id IN (%(id)s)
        """ % {'language': self.language, 'id': ','.join(map(str, entity_definition_id))}
        # logging.debug(sql)

        return self.db.query(sql)

    def get_relatives(self, ids_only=False, relationship_ids_only=False, entity_id=None, related_entity_id=None, relation_type=None, reverse_relation=False, entity_definition_id=None, full_definition=False, limit=None, only_public=False):
        """
        Get Entity relatives.

        """
        if entity_id:
            if type(entity_id) is not list:
                entity_id = [entity_id]

        if related_entity_id:
            if type(related_entity_id) is not list:
                related_entity_id = [related_entity_id]

        if relation_type:
            if type(relation_type) is not list:
                relation_type = [relation_type]

        if entity_definition_id:
            if type(entity_definition_id) is not list:
                entity_definition_id = [entity_definition_id]

        if reverse_relation == True:
            sql = """
                SELECT DISTINCT
                    relationship.id AS relationship_id,
                    relationship_definition.type,
                    relationship.entity_id AS id
                FROM
                    entity,
                    relationship,
                    relationship_definition,
                    relationship AS rights,
                    relationship_definition AS rights_definition
                WHERE relationship.entity_id = entity.id
                AND relationship_definition.id = relationship.relationship_definition_id
                AND rights.entity_id = entity.id
                AND rights_definition.id = rights.relationship_definition_id
                AND relationship.deleted IS NULL
            """
            if entity_id:
                sql += ' AND relationship.related_entity_id IN (%s)' % ','.join(map(str, entity_id))
            if related_entity_id:
                sql += ' AND relationship.entity_id IN (%s)' % ','.join(map(str, related_entity_id))
        else:
            sql = """
                SELECT DISTINCT
                    relationship.id AS relationship_id,
                    relationship_definition.type,
                    relationship.related_entity_id AS id
                FROM
                    entity,
                    relationship,
                    relationship_definition,
                    relationship AS rights,
                    relationship_definition AS rights_definition
                WHERE relationship.related_entity_id = entity.id
                AND relationship_definition.id = relationship.relationship_definition_id
                AND rights.entity_id = entity.id
                AND rights_definition.id = rights.relationship_definition_id
                AND relationship.deleted IS NULL
            """
            if entity_id:
                sql += ' AND relationship.entity_id IN (%s)' % ','.join(map(str, entity_id))
            if related_entity_id:
                sql += ' AND relationship.related_entity_id IN (%s)' % ','.join(map(str, related_entity_id))

        if self.user_id and only_public == False:
            sql += ' AND rights.related_entity_id IN (%s) AND rights_definition.type IN (\'leecher\', \'viewer\', \'editor\', \'owner\')' % ','.join(map(str, self.user_id))
        else:
            sql += ' AND entity.public = 1'

        if relation_type:
            sql += ' AND relationship_definition.type IN (%s)' % ','.join(['\'%s\'' % x for x in relation_type])

        if entity_definition_id:
            sql += ' AND entity.entity_definition_id IN (%s)' % ','.join(map(str, entity_definition_id))

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
                ent = self.__get_properties(entity_id=item.id, full_definition=full_definition, entity_definition_id=entity_definition_id, only_public=only_public)
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
            AND property_definition.id = property.property_definition_id
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

    def get_entity_definition(self, entity_definition_id):
        """
        Returns entity_definition.

        """
        if entity_definition_id:
            if type(entity_definition_id) is not list:
                entity_definition_id = [entity_definition_id]

        sql = """
            SELECT
                id,
                %(language)s_label AS label,
                %(language)s_label_plural AS label_plural,
                %(language)s_description AS description,
                %(language)s_menu AS menugroup,
                ordinal
            FROM
                entity_definition
            WHERE id IN (%(ids)s);
        """  % {'language': self.language, 'ids': ','.join(map(str, entity_definition_id))}
        logging.debug(sql)

        return self.db.query(sql)

    def get_allowed_childs(self, entity_id):
        """
        Returns allowed child definitions.

        """
        sql = """
            SELECT
                entity_definition.id,
                entity_definition.%(language)s_label AS label,
                entity_definition.%(language)s_label_plural AS label_plural,
                entity_definition.%(language)s_description AS description,
                entity_definition.%(language)s_menu AS menugroup
            FROM
                entity_definition,
                relationship,
                relationship_definition
            WHERE relationship.related_entity_definition_id = entity_definition.id
            AND relationship_definition.id = relationship.relationship_definition_id
            AND relationship_definition.type = 'allowed_child'
            AND relationship.entity_id = %(id)s
        """  % {'language': self.language, 'id': entity_id}
        # logging.debug(sql)

        result = self.db.query(sql)
        if result:
            return result

        sql = """
            SELECT
                entity_definition.id,
                entity_definition.%(language)s_label AS label,
                entity_definition.%(language)s_label_plural AS label_plural,
                entity_definition.%(language)s_description AS description,
                entity_definition.%(language)s_menu AS menugroup
            FROM
                entity_definition,
                relationship,
                relationship_definition
            WHERE relationship.related_entity_definition_id = entity_definition.id
            AND relationship_definition.id = relationship.relationship_definition_id
            AND relationship_definition.type = 'allowed_child'
            AND relationship.entity_definition_id = (SELECT entity_definition_id FROM entity WHERE id = %(id)s)
        """  % {'language': self.language, 'id': entity_id}
        # logging.debug(sql)

        return self.db.query(sql)

    def get_menu(self):
        """
        Returns user menu.

        """

        sql = """
            SELECT DISTINCT
                entity_definition.id,
                entity_definition.%(language)s_menu AS menugroup,
                entity_definition.%(language)s_label AS item
            FROM
                entity_definition,
                entity,
                relationship,
                relationship_definition
            WHERE entity.entity_definition_id = entity_definition.id
            AND relationship.entity_id = entity.id
            AND relationship_definition.id = relationship.relationship_definition_id
            AND relationship_definition.type IN ('leecher', 'viewer', 'editor', 'owner')
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
            menu.setdefault(m.menugroup, {}).setdefault('items', []).append({'id': m.id, 'title': m.item})

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
            WHERE property.property_definition_id = property_definition.id
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
