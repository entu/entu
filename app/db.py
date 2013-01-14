from tornado import database
from tornado import locale
from tornado.options import options

from operator import itemgetter
from datetime import datetime

import random
import string
import hashlib
import time
import logging
import hashlib
import re
import math


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
        self.created_by     = ''

        if user_id:
            if type(self.user_id) is not list:
                self.user_id = [self.user_id]
            self.created_by = ','.join(map(str, self.user_id))

        # logging.debug({'user':self.user_id, 'created':self.created_by})


    def create(self, entity_definition_keyname, parent_entity_id=None):
        """
        Creates new Entity and returns its ID.

        """
        logging.debug('creating %s under entity %s' % (entity_definition_keyname, parent_entity_id))
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

        # Insert child relationship from default parent
        sql = """
            INSERT INTO relationship (
                relationship_definition_keyname,
                entity_id,
                related_entity_id,
                created_by,
                created
            ) SELECT /* SQL_NO_CACHE */
                'child',
                r.related_entity_id,
                %s,
                %s,
                NOW()
            FROM relationship AS r
            WHERE r.relationship_definition_keyname = 'default-parent'
            AND r.deleted IS NULL
            AND r.entity_definition_keyname = %s;
        """
        # logging.debug(sql)
        self.db.execute(sql, entity_id, self.created_by, entity_definition_keyname)

        # Insert or update "contains" information
        for row in self.db.query("SELECT entity_id FROM relationship r WHERE relationship_definition_keyname = 'child' AND related_entity_id = %s" , entity_id):
            self.db.execute('INSERT INTO dag_entity SET entity_id = %s, related_entity_id = %s ON DUPLICATE KEY UPDATE distance=1;', row.entity_id, entity_id)
            self.db.execute('INSERT INTO dag_entity SELECT de.entity_id, %s, de.distance+1 FROM dag_entity AS de WHERE de.related_entity_id = %s ON DUPLICATE KEY UPDATE distance = LEAST(dag_entity.distance, de.distance+1);', entity_id, row.entity_id)

        # Copy user rights
        sql = """
            INSERT INTO relationship (
                relationship_definition_keyname,
                entity_id,
                related_entity_id,
                created_by,
                created
            ) SELECT /* SQL_NO_CACHE */
                rr.relationship_definition_keyname,
                %s,
                rr.related_entity_id,
                %s,
                NOW()
            FROM      relationship r
            LEFT JOIN relationship rr ON rr.entity_id = r.entity_id
            WHERE     r.deleted IS NULL
            AND       r.related_entity_id = %s
            AND       r.relationship_definition_keyname = 'child'
            AND       rr.relationship_definition_keyname IN ('leecher', 'viewer', 'editor', 'owner' );
        """
        # logging.debug(sql)
        self.db.execute(sql, entity_id, self.created_by, entity_id)

        # Populate default values
        for default_value in self.db.query('SELECT keyname, defaultvalue FROM property_definition WHERE entity_definition_keyname = %s AND defaultvalue IS NOT null', entity_definition_keyname):
            self.set_property(entity_id=entity_id, property_definition_keyname=default_value.keyname, value=default_value.defaultvalue)

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
                r.related_property_definition_keyname,
                p.language,
                p.value_string,
                p.value_text,
                p.value_integer,
                p.value_decimal,
                p.value_boolean,
                p.value_datetime,
                p.value_entity,
                p.value_file,
                p.value_counter,
                %s,
                NOW()
            FROM
                relationship AS r,
                property_definition AS pd,
                property AS p
            WHERE pd.keyname = r.property_definition_keyname
            AND p.property_definition_keyname = pd.keyname
            AND pd.entity_definition_keyname = %s
            AND p.entity_id = %s
            AND r.relationship_definition_keyname = 'propagated_property'
            AND p.deleted IS NULL
            AND r.deleted IS NULL
            ;
        """
        # logging.debug(sql)
        self.db.execute(sql, entity_id, self.created_by, entity_definition_keyname, parent_entity_id)

        return entity_id

    def set_property(self, entity_id=None, relationship_id=None, property_definition_keyname=None, value=None, old_property_id=None, uploaded_file=None):
        """
        Saves property value. Creates new one if old_property_id = None. Returns new_property_id.

        """
        if not entity_id:
            return

        # property_definition_keyname is preferred because it could change for existing property
        if property_definition_keyname:
            definition = self.db.get('SELECT datatype, formula FROM property_definition WHERE keyname = %s LIMIT 1;', property_definition_keyname)
        elif old_property_id:
            definition = self.db.get('SELECT pd.datatype, pd.formula FROM property p LEFT JOIN property_definition pd ON pd.keyname = p.property_definition_keyname WHERE p.id = %s;', old_property_id)
        else:
            return

        if not definition:
            return

        if old_property_id:
            self.db.execute('UPDATE property SET deleted = NOW(), deleted_by = %s WHERE id = %s;', self.created_by, old_property_id )
            if definition.formula == 1:
                Formula(user_locale=self.user_locale, created_by=self.created_by, entity_id=entity_id, property_id=old_property_id).delete()


        # If no value, then property is deleted, return
        if not value:
            return

        new_property_id = self.db.execute_lastrowid('INSERT INTO property SET entity_id = %s, property_definition_keyname = %s, created = NOW(), created_by = %s;',
            entity_id,
            property_definition_keyname,
            self.created_by
        )

        if definition.formula == 1:
            formula = Formula(user_locale=self.user_locale, created_by=self.created_by, entity_id=entity_id, property_id=new_property_id, formula=value)
            value = ''.join(formula.evaluate())

        if definition.datatype in ['text', 'html']:
            field = 'value_text'
        elif definition.datatype == 'integer':
            field = 'value_integer'
        elif definition.datatype == 'decimal':
            field = 'value_decimal'
            value = value.replace(',', '.')
            value = re.sub(r'[^\.0-9:]', '', value)
        elif definition.datatype == 'date':
            field = 'value_datetime'
        elif definition.datatype == 'datetime':
            field = 'value_datetime'
        elif definition.datatype == 'file':
            uploaded_file = value
            value = self.db.execute_lastrowid('INSERT INTO file SET filename = %s, filesize = %s, file = %s, created_by = %s, created = NOW();', uploaded_file['filename'], len(uploaded_file['body']), uploaded_file['body'], self.created_by)
            field = 'value_file'
        elif definition.datatype == 'boolean':
            field = 'value_boolean'
            value = 1 if value.lower() == 'true' else 0
        elif definition.datatype == 'counter':
            field = 'value_counter'
        else:
            field = 'value_string'
            value = value[:500]

        # logging.debug('UPDATE property SET %s = %s WHERE id = %s;' % (field, value, new_property_id) )

        self.db.execute('UPDATE property SET %s = %%s WHERE id = %%s;' % field, value, new_property_id )

        if definition.formula == 1:
            formula.save_property(new_property_id=new_property_id, old_property_id=old_property_id)
        else:
            Formula(user_locale=self.user_locale, created_by=self.created_by, entity_id=entity_id, property_id=new_property_id).update_depending_formulas()

        self.db.execute('UPDATE entity SET changed = NOW(), changed_by = %s WHERE id = %s;',
            self.created_by,
            entity_id,
        )

        return new_property_id

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
        Counter mechanics is real hack. It will soon be obsoleted by formula field.
        """
        if not entity_id:
            return

        #Vastuskirja hack
        if self.db.get('SELECT entity_definition_keyname FROM entity WHERE id = %s', entity_id).entity_definition_keyname == 'reply':
            parent = self.get_relatives(related_entity_id=entity_id, relationship_definition_keyname='child', reverse_relation=True, limit=1).values()[0][0]
            childs = self.get_relatives(entity_id=parent.get('id',None), relationship_definition_keyname='child').values()
            if childs:
                childs_count = len([y.get('id', 0) for y in childs[0] if y.get('properties', {}).get('registry-number', {}).get('values', None)])+1
            else:
                childs_count = 1
            parent_number = ''.join(['%s' % x['value'] for x in parent.get('properties', {}).get('registry-number', {}).get('values', []) if x['value']])
            counter_value = '%s-%s' % (parent_number, childs_count)
            self.set_property(entity_id=entity_id, property_definition_keyname='reply-registry-number', value=counter_value)
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
                    AND property_definition.dataproperty = 'series'
                    AND entity.id = (SELECT entity_id FROM relationship WHERE related_entity_id = %(entity_id)s AND relationship_definition_keyname = 'child' LIMIT 1)
                    AND entity.deleted IS NULL
                    AND property.deleted IS NULL
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
                    AND entity.deleted IS NULL
                    AND property.deleted IS NULL
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
            AND relationship.deleted IS NULL
            AND property.deleted IS NULL
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
                AND relationship.deleted IS NULL
                AND property.deleted IS NULL
                ) X
            SET
                counter.value = counter.value + counter.increment,
                counter.changed_by = '%(user_id)s',
                counter.changed = NOW()
            WHERE counter.id = X.id;
        """ % {'entity_id': entity_id, 'user_id': ','.join(map(str, self.user_id))}
        # logging.debug(sql)

        property_id = self.db.execute_lastrowid(sql)
        # logging.warning(str(property_id))
        return self.db.get('SELECT value_string FROM property WHERE id = %s', property_id).value_string

    def set_relations(self, entity_id, related_entity_id, relationship_definition_keyname, delete=False, update=False):
        """
        Adds or removes Entity relations. entity_id, related_entity_id, relationship_definition_keyname can be single value or list of values.

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
        If ids_only = True, then returns list of Entity IDs. Else returns list of Entities (with properties) as dictionary. entity_id, entity_definition and dataproperty can be single value or list of values.
        If limit = 1, then returns Entity (not list).
        If full_definition = True ,then returns also empty properties.

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
            AND entity.deleted IS NULL
            AND property.deleted IS NULL
            AND relationship.deleted IS NULL
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

    def formula_properties(self, entity_id):
        sql = """
            SELECT *
            FROM property p
            WHERE p.entity_id = %s
            AND p.value_formula is not null
            AND p.deleted is null
            ORDER BY p.id
            ;""" % entity_id
        # logging.debug(sql)
        return self.db.query(sql)

    def __get_properties(self, entity_id=None, entity_definition_keyname=None, dataproperty=None, full_definition=False, only_public=False):
        """
        Get Entity properties. entity_id can be single ID or list of IDs.
        * full_definition - All metadata for entity and properties is fetched, if True
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
                    entity.changed                                  AS entity_changed,
                    entity.public                                   AS entity_public,
                    entity_definition.%(language)s_displayname      AS entity_displayname,
                    entity_definition.%(language)s_displayinfo      AS entity_displayinfo,
                    entity_definition.%(language)s_displaytable     AS entity_displaytable,
                    entity_definition.%(language)s_sort             AS entity_sort,
                    entity.sort                                     AS entity_sort_value,
                    property_definition.keyname                     AS property_keyname,
                    property_definition.ordinal                     AS property_ordinal,
                    property_definition.formula                     AS property_formula,
                    property_definition.executable                  AS property_executable,
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
                    property.value_formula                          AS value_formula,
                    property.value_string                           AS value_string,
                    property.value_text                             AS value_text,
                    property.value_integer                          AS value_integer,
                    property.value_decimal                          AS value_decimal,
                    property.value_boolean                          AS value_boolean,
                    property.value_datetime                         AS value_datetime,
                    property.value_entity                           AS value_entity,
                    property.value_counter                          AS value_counter,
                    property.value_reference                        AS value_reference,
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
                AND entity.deleted IS NULL
                AND property.deleted IS NULL
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
                items.setdefault('item_%s' % row.entity_id, {})['created'] = row.entity_created
                items.setdefault('item_%s' % row.entity_id, {})['changed'] = row.entity_changed
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
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['formula'] = True if row.property_formula == 1 else False
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['executable'] = True if row.property_executable == 1 else False
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
                    value = '%.2f' % row.value_decimal
                elif row.property_datatype == 'date':
                    db_value = row.value_datetime
                    value = formatDatetime(row.value_datetime, '%(day)02d.%(month)02d.%(year)d')
                elif row.property_datatype == 'datetime':
                    db_value = row.value_datetime
                    value = formatDatetime(row.value_datetime)
                elif row.property_datatype == 'reference':
                    value = ''
                    if row.value_reference:
                        reference = self.__get_properties(entity_id=row.value_reference)
                        if reference:
                            value = reference[0].get('displayname')
                    # logging.debug(str(reference))
                    db_value = row.value_entity
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

                # Formula
                if row.property_formula == 1:
                    # value = '%s (%s)' % (value, row.value_formula)
                    db_value = row.value_formula

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
                dataproperty_dict = entity_dict.get('properties', {}).get(data_property, {})
                # logging.debug(dataproperty_dict)
                if displayfield == 'sort' and dataproperty_dict.get('datatype') == 'date':
                    result[displayfield] = result[displayfield].replace('@%s@' % data_property, ', '.join(['%s' % sortableDateTime(x['db_value']) for x in dataproperty_dict.get('values', {}).values()]))
                elif displayfield == 'sort' and dataproperty_dict.get('datatype') == 'integer':
                    result[displayfield] = result[displayfield].replace('@%s@' % data_property, ', '.join(['%s' % sortableInteger(x['db_value']) for x in dataproperty_dict.get('values', {}).values()]))
                elif displayfield == 'sort' and dataproperty_dict.get('datatype') == 'decimal':
                    result[displayfield] = result[displayfield].replace('@%s@' % data_property, ', '.join(['%s' % sortableDecimal(x['db_value']) for x in dataproperty_dict.get('values', {}).values()]))
                else:
                    result[displayfield] = result[displayfield].replace('@%s@' % data_property, ', '.join(['%s' % x['value'] for x in dataproperty_dict.get('values', {}).values()]))
                result[displayfield] = result[displayfield].replace('\n', ' ')

        result['displaytable_labels'] = entity_dict.get('displaytable', '') if entity_dict.get('displaytable', '') else ''
        for data_property in findTags(entity_dict.get('displaytable', ''), '@', '@'):
            result['displaytable_labels'] = result['displaytable_labels'].replace('@%s@' % data_property, entity_dict.get('properties', {}).get(data_property, {}).get('label', ''))

        result['displaytable'] = result['displaytable'].split('|') if result['displaytable'] else None
        result['displaytable_labels'] = result['displaytable_labels'].split('|') if result['displaytable_labels'] else None

        if entity_dict.get('id', None) and entity_dict.get('sort_value', None) != result['sort']:
            self.db.execute('UPDATE entity SET sort = LEFT(%s, 100) WHERE id = %s', result['sort'], entity_dict.get('id'))

        return result

    def __get_picture_url(self, entity_id):
        """
        Returns Entity picture.

        """
        sql = """
            SELECT
                f.id
            FROM
                property,
                property_definition,
                file f
            WHERE property_definition.keyname=property.property_definition_keyname
            AND f.id = property.value_file
            AND property_definition.dataproperty='photo'
            AND property.entity_id = %s
            AND property.deleted IS NULL
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
        * ids_only, relationship_ids_only - return only respective id's if True; return full info by default (False, False).
          (True, True) is interpreted as (True, False)
        * entity_id - find only relations for these entities
        * related_entity_id - find only relations for these related entities
        * relationship_definition_keyname - find only relations with these relationship types
        * reverse_relation - obsolete. Just give related_entity_id instead of entity_id
        * entity_definition_keyname - find only relations with entities of these entity types
        * full_definition - parameter gets forwarded to Entity.__get_properties
        * limit - MySQL-specific limit
        * only_public - if True then only public entities are fetched, othervise user rights are checked. Also gets forwarded to Entity.__get_properties
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
                    r.id AS relationship_id,
                    r.relationship_definition_keyname,
                    r.entity_id AS id
                FROM
                    entity AS e,
                    relationship AS r,
                    relationship AS rights
                WHERE r.entity_id = e.id
                AND rights.entity_id = e.id
                AND r.deleted IS NULL
                AND rights.deleted IS NULL
                AND e.deleted IS NULL
            """
        else:
            sql = """
                SELECT DISTINCT
                    r.id AS relationship_id,
                    r.relationship_definition_keyname,
                    r.related_entity_id AS id
                FROM
                    entity AS e,
                    relationship AS r,
                    relationship AS rights
                WHERE r.related_entity_id = e.id
                AND rights.entity_id = e.id
                AND r.deleted IS NULL
                AND rights.deleted IS NULL
                AND e.deleted IS NULL
            """

        if entity_id:
            sql += ' AND r.entity_id IN (%s)' % ','.join(map(str, entity_id))

        if related_entity_id:
            sql += ' AND r.related_entity_id IN (%s)' % ','.join(map(str, related_entity_id))

        if self.user_id and only_public == False:
            sql += ' AND rights.related_entity_id IN (%s) AND rights.relationship_definition_keyname IN (\'leecher\', \'viewer\', \'editor\', \'owner\')' % ','.join(map(str, self.user_id))
        else:
            sql += ' AND e.public = 1'

        if relationship_definition_keyname:
            sql += ' AND r.relationship_definition_keyname IN (%s)' % ','.join(['\'%s\'' % x for x in relationship_definition_keyname])

        if entity_definition_keyname:
            sql += ' AND e.entity_definition_keyname IN (%s)' % ','.join(map(str, entity_definition_keyname))

        sql += ' ORDER BY e.sort, e.created DESC'

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
        return items

    def get_file(self, file_id):
        """
        Returns file object. File properties are id, file, filename.

        """

        if type(file_id) is not list:
            file_id = [file_id]

        if self.user_id:
            public = ''
        else:
            public = 'AND property_definition.public = 1'

        sql = """
            SELECT
                f.id,
                f.created,
                f.file,
                f.filename
            FROM
                file AS f,
                property AS p,
                property_definition AS pd
            WHERE p.value_file = f.id
            AND pd.keyname = p.property_definition_keyname
            AND f.id IN (%(file_id)s)
            %(public)s
            AND p.deleted IS NULL
            """ % {'file_id': ','.join(map(str, file_id)), 'public': public}
        # logging.debug(sql)

        return self.db.query(sql)

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
                entity_definition.open_after_add,
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
                ed.keyname,
                ed.%(language)s_label AS label,
                ed.%(language)s_label_plural AS label_plural,
                ed.%(language)s_description AS description,
                ed.%(language)s_menu AS menugroup
            FROM
                relationship r
                LEFT JOIN entity_definition ed ON r.related_entity_definition_keyname = ed.keyname
            WHERE r.relationship_definition_keyname = 'allowed-child'
            AND r.entity_id = %(id)s
            AND r.deleted IS NULL
            ORDER BY ed.keyname        """  % {'language': self.language, 'id': entity_id}
        # logging.debug(sql)

        result = self.db.query(sql)
        if result:
            if not result[0].keyname:
                return []
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
            AND relationship.deleted IS NULL
        """  % {'language': self.language, 'id': entity_id}
        # logging.debug(sql)

        return self.db.query(sql)

    def get_definitions_with_default_parent(self, entity_definition_keyname):
        """
        Returns allowed entity definitions what have default parent.

        """

        if entity_definition_keyname:
            if type(entity_definition_keyname) is not list:
                entity_definition_keyname = [entity_definition_keyname]

        sql = """
            SELECT DISTINCT
                entity_definition.keyname,
                entity_definition.%(language)s_label AS label,
                entity_definition.%(language)s_label_plural AS label_plural,
                entity_definition.%(language)s_description AS description,
                entity_definition.%(language)s_menu AS menugroup,
                relationship.related_entity_id
            FROM
                entity_definition,
                relationship
            WHERE relationship.entity_definition_keyname = entity_definition.keyname
            AND relationship.relationship_definition_keyname = 'default-parent'
            AND entity_definition.keyname IN (%(ids)s)
            AND relationship.deleted IS NULL
        """  % {'language': self.language, 'ids': ','.join(['\'%s\'' % x for x in map(str, entity_definition_keyname)])}
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
            AND entity.deleted IS NULL
            AND relationship.deleted IS NULL
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

    def delete(self, entity_id):
        for child_id in self.get_relatives(ids_only=True, entity_id=entity_id, relationship_definition_keyname='child'):
            self.delete(child_id)

        self.db.execute('UPDATE entity SET deleted = NOW(), deleted_by = %s WHERE id = %s;', self.created_by, entity_id)

        # remove "contains" information
        self.db.execute('DELETE FROM dag_entity WHERE entity_id = %s OR related_entity_id = %s;', entity_id, entity_id)


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
                user.provider
            FROM
                property_definition,
                property,
                entity,
                user
            WHERE property.property_definition_keyname = property_definition.keyname
            AND entity.id = property.entity_id
            AND property.deleted IS NULL
            AND entity.deleted IS NULL
            AND user.email = property.value_string
            AND property_definition.dataproperty = 'user'
            AND user.session = %s
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

    def login(self, request_handler, session_key=None, provider=None, provider_id=None, email=None, name=None, picture=None):
        """
        Starts session. Creates new (or updates old) user.

        """
        if not session_key:
            session_key = str(''.join(random.choice(string.ascii_letters + string.digits) for x in range(32)) + hashlib.md5(str(time.time())).hexdigest())
        user_key = hashlib.md5(request_handler.request.remote_ip + request_handler.request.headers.get('User-Agent', None)).hexdigest()


        db = connection()
        profile_id = db.execute_lastrowid('INSERT INTO user SET provider = %s, provider_id = %s, email = %s, name = %s, picture = %s, language = %s, session = %s, created = NOW() ON DUPLICATE KEY UPDATE email = %s, name = %s, picture = %s, session = %s, changed = NOW();',
                provider,
                provider_id,
                email,
                name,
                picture,
                request_handler.settings['default_language'],
                session_key+user_key,
                email,
                name,
                picture,
                session_key+user_key
            )

        request_handler.set_secure_cookie('session', session_key)

        return session_key


class Formula():
    """
    entity_id is accessed from FExpression.fetch_path_from_db() method
    """
    def __init__(self, user_locale, created_by, property_id, formula=None, entity_id=None):
        self.db                     = connection()
        self.formula                = formula
        self.entity_id              = entity_id
        self.value                  = []
        self.dependencies           = []
        self.user_locale            = user_locale
        self.language               = user_locale.code
        self.created_by             = created_by

        self.dag_stack              = Queue()
        self.dag_failed             = False
        self.formula_property_id    = property_id

        # logging.debug('Formula.init')
        self.create_dag()

    def delete(self):
        """
        Mark property's dependencies as deleted and revaluate formulas that were depending on property.
        Then mark explicit DAG relations as deleted.
        """
        self.db.execute('UPDATE dag_formula SET deleted = NOW(), deleted_by = %s WHERE property_id = %s;', self.created_by, self.formula_property_id )
        self.update_depending_formulas()
        self.db.execute('UPDATE dag_formula SET deleted = NOW(), deleted_by = %s WHERE related_property_id = %s;', self.created_by, self.formula_property_id )

    def evaluate(self):
        if not self.formula:
            return ''
        if self.dag_failed:
            return 'E: Formula has recursive dependency.'

        for m in re.findall(r"([^{]*){([^{}]*)}|(.*?)$",self.formula):
            if m[0]:
                self.value.append(m[0].encode('utf8'))
            if m[1]:
                self.value.append('%s'.encode('utf8') % ','.join(map(str, FExpression(self, m[1]).value)))
            if m[2]:
                self.value.append(m[2].encode('utf8'))

        return self.value

    def save_property(self, new_property_id, old_property_id):

        if old_property_id:
            for row in self.db.query('SELECT property_id FROM dag_formula WHERE related_property_id = %s AND deleted IS NULL', old_property_id):
                self.db.execute('INSERT INTO dag_formula SET created = NOW(), created_by = %s, property_id = %s, related_property_id = %s;', self.created_by, row.property_id, new_property_id)
            self.db.execute('UPDATE dag_formula SET deleted = NOW(), deleted_by = %s WHERE related_property_id = %s;', self.created_by, old_property_id)

        self.db.execute('UPDATE property SET value_formula = %s WHERE id = %s;', self.formula, new_property_id)

        # Create formula DAG dependencies
        # logging.debug(self.dependencies)
        for dependency in self.dependencies:
            # logging.debug(dependency)
            self.db.execute('INSERT INTO dag_formula SET created = NOW(), created_by = %s, property_id = %s, related_property_id = %s, entity_id = %s, dataproperty = %s, relationship_definition_keyname = %s, reverse_relationship = %s, entity_definition_keyname = %s;', self.created_by, new_property_id, dependency.get('related_property_id',None), dependency.get('entity_id',None), dependency.get('dataproperty',None), dependency.get('relationship_definition_keyname',None), dependency.get('reverse_relationship',None), dependency.get('entity_definition_keyname',None))

    def update_depending_formulas(self):
        while not self.dag_stack.isEmpty:
            property_id = self.dag_stack.pop()
            db_property = self.db.get('SELECT value_formula, entity_id FROM property WHERE id = %s', property_id)
            # logging.debug(db_property)
            formula = Formula(user_locale=self.user_locale, created_by=self.created_by, formula=db_property.value_formula, entity_id=db_property.entity_id, property_id=property_id)
            value = ''.join(formula.evaluate())
            self.db.execute('UPDATE property SET value_string = %s WHERE id = %s', value, property_id)
            # logging.debug(value)

        # logging.debug('update_depending_formulas')
        self.create_dag()
        return True

    def create_dag(self, property_id_in=None):
        if property_id_in == None:
            property_id_in = self.formula_property_id
        if not property_id_in == self.formula_property_id:
            self.dag_stack.push(property_id_in)

        rowset = []

        sql = """
            -- Matches explicit dependencies
            SELECT df.id, df.property_id
            FROM dag_formula AS df
            WHERE  df.deleted IS NULL
            AND    df.related_property_id = %s """ % property_id_in
        # logging.debug(sql)
        for row in self.db.query(sql):
            if row not in rowset:
                rowset.append(row)
        # logging.debug(rowset)

        sql = """
            -- Matches self.dataproperty and id.dataproperty
            SELECT df.id, df.property_id
            FROM dag_formula AS df
            LEFT JOIN property AS p ON p.entity_id = df.entity_id
            LEFT JOIN property_definition AS pd ON (pd.keyname = p.property_definition_keyname)
            WHERE  df.deleted IS NULL
            AND    df.related_property_id IS NULL
            AND    df.relationship_definition_keyname IS NULL
            AND    df.reverse_relationship IS NULL
            AND    df.entity_definition_keyname IS NULL
            AND    pd.dataproperty = df.dataproperty
            AND     p.id = %s """ % property_id_in
        # logging.debug(sql)
        for row in self.db.query(sql):
            if row not in rowset:
                rowset.append(row)
        # logging.debug(rowset)

        sql = """
            -- Matches self.rdk.edk.dataproperty, self.rdk.*.dataproperty, id.rdk.edk.dataproperty and id.rdk.*.dataproperty
            SELECT df.id, df.property_id
            FROM dag_formula AS df
            LEFT JOIN relationship AS r ON (r.entity_id = df.entity_id AND r.relationship_definition_keyname = df.relationship_definition_keyname)
            LEFT JOIN entity AS e ON (e.id = r.related_entity_id AND (e.entity_definition_keyname = df.entity_definition_keyname OR df.entity_definition_keyname IS NULL))
            LEFT JOIN property AS p ON (p.entity_id = e.id)
            LEFT JOIN property_definition AS pd ON (pd.keyname = p.property_definition_keyname AND pd.dataproperty = df.dataproperty)
            WHERE  df.deleted IS NULL
            AND     r.deleted IS NULL
            AND    df.related_property_id IS NULL
            AND    df.reverse_relationship IS NULL
            AND     p.id = %s """ % property_id_in
        # logging.debug(sql)
        # rowset = list(set(rowset + self.db.query(sql)))
        for row in self.db.query(sql):
            if row not in rowset:
                rowset.append(row)
        # rowset = list(set(rowset + self.db.query(sql)))
        # logging.debug(rowset)

        sql = """
            -- Matches self.-rdk.edk.dataproperty, self.-rdk.*.dataproperty, id.-rdk.edk.dataproperty and id.-rdk.*.dataproperty
            SELECT df.id, df.property_id
            FROM dag_formula AS df
            LEFT JOIN relationship AS r ON (r.related_entity_id = df.entity_id AND r.relationship_definition_keyname = df.relationship_definition_keyname)
            LEFT JOIN entity AS e ON (e.id = r.entity_id AND (e.entity_definition_keyname = df.entity_definition_keyname OR df.entity_definition_keyname IS NULL))
            LEFT JOIN property AS p ON (p.entity_id = e.id)
            LEFT JOIN property_definition AS pd ON (pd.keyname = p.property_definition_keyname AND pd.dataproperty = df.dataproperty)
            WHERE  df.deleted IS NULL
            AND     r.deleted IS NULL
            AND    df.related_property_id IS NULL
            AND    df.reverse_relationship = 1
            AND     p.id = %s """ % property_id_in
        # logging.debug(sql)
        for row in self.db.query(sql):
            if row not in rowset:
                rowset.append(row)
        # logging.debug(rowset)

        for row in rowset:
            # logging.debug(row)
            property_id = row.property_id

            if property_id == self.formula_property_id:
                self.dag_failed = True
                return False

            if self.dag_stack.check(property_id):
                continue

            # logging.debug('create_dag')
            self.create_dag(property_id)

        return not self.dag_failed


class FExpression():

    def __init__(self, formula, xpr):
        self.db             = connection()
        self.formula        = formula
        self.xpr            = re.sub(' ', '', xpr)
        self.value          = []

        # logging.debug(self.xpr)

        if not self.parcheck():
            self.value = "ERROR"
            return self.value

        re.sub(r"(.*?)([A-Z]+)\(([^\)]*)\)", mdbg, self.xpr)

        for m in re.findall(r"(.*?)([A-Z]+)\(([^\)]*)\)",self.xpr):
            self.value.append('%s%s' % (m[0], self.evalfunc(m[1], m[2])))
            # self.value.append('%s%s' % (m[0], ','.join(self.evalfunc(m[1], m[2]))))

        if self.value == []:
            _values = []
            for row in self.fetch_path_from_db(self.xpr):
                # logging.debug(row.value)
                _values.append(row.value)

            self.value = [', '.join(map(str,_values))]
            # logging.debug(self.value)

        # logging.debug(re.findall(r"(.*?)([A-Z]+)\(([^\)]*)\)",self.xpr))
        # logging.debug(self.value)
        # self.value = map(eval, self.value)
        # logging.debug(self.value)

    def evalfunc(self, fname, path):
        FFunc = {
            'SUM' : self.FE_sum,
            'MIN' : self.FE_min,
            'MAX' : self.FE_max,
            'COUNT' : self.FE_count,
            'AVERAGE' : self.FE_average,
        }
        # logging.debug(FFunc[fname](self.fetch_path_from_db(path)))
        return FFunc[fname](self.fetch_path_from_db(path))

    def FE_sum(self, items):
        return 30.3

    def FE_min(self, items):
        return 30.3

    def FE_max(self, items):
        return 30.3

    def FE_average(self, items):
        return 30.3
        # math.fsum(items)

    def FE_count(self, items):
        return len(items)

    def fetch_path_from_db(self, path):
        """
        https://github.com/argoroots/Entu/blob/master/docs/Formula.md
        """
        tokens = re.split('\.', path)
        # logging.debug(tokens)

        if len(tokens) < 2:
            return []

        if tokens[0] == 'self':
            tokens[0] = self.formula.entity_id

        # Prepare formula dependencies
        dependency = {'entity_id': tokens[0]}

        # Entity id:{self.id} is called {self.name}; and id:{6.id} description is {6.description}
        if len(tokens) == 2:
            if tokens[1] == '':
                tokens[1] = 'id'

            sql = 'SELECT ifnull(p.value_decimal, ifnull(p.value_string, ifnull(p.value_text, ifnull(p.value_integer, ifnull(p.value_datetime, ifnull(p.value_boolean, p.value_file)))))) as value'
            if tokens[1] == 'id':
                sql = 'SELECT e.id as value'

            sql += """
                FROM entity e
            """

            if tokens[1] != 'id':
                sql += """
                    LEFT JOIN property p ON p.entity_id = e.id
                    LEFT JOIN property_definition pd ON pd.keyname = p.property_definition_keyname
                """

            sql += """
                WHERE e.id = %(entity_id)s
                AND e.deleted IS NULL
            """  % {'entity_id': tokens[0]}

            if tokens[1] != 'id':
                sql += """
                    AND p.deleted IS NULL
                    AND pd.dataproperty = '%(pdk)s'
                """ % {'pdk': tokens[1]}

            # logging.debug(sql)

            result = self.db.query(sql)

            # Prepare formula dependencies
            # Entity {self.id} is called {self.name}, but {12.id} is called {12.name}
            if tokens[1] != 'id':
                dependency['dataproperty'] = tokens[1]

            self.formula.dependencies.append(dependency)
            return result


        if len(tokens) != 4:
            return []

        if tokens[3] == '':
            tokens[3] = 'id'

        sql = 'SELECT ifnull(p.value_decimal, ifnull(p.value_string, ifnull(p.value_text, ifnull(p.value_integer, ifnull(p.value_datetime, ifnull(p.value_boolean, p.value_file)))))) as value'
        if tokens[3] == 'id':
            sql = 'SELECT re.id as value'

        _entity = 'entity'
        _related_entity = 'related_entity'
        if tokens[1][:1] == '-':
            _entity = 'related_entity'
            _related_entity = 'entity'
            tokens[1] = tokens[1][1:]

        sql += """
            FROM entity e
            LEFT JOIN relationship r ON r.%(entity)s_id = e.id
            LEFT JOIN entity re ON re.id = r.%(related_entity)s_id
        """ % {'entity': _entity, 'related_entity': _related_entity}

        if tokens[3] != 'id':
            sql += """
                LEFT JOIN property p ON p.entity_id = re.id
                LEFT JOIN property_definition pd ON pd.keyname = p.property_definition_keyname
            """

        sql += """
            WHERE e.id = %(entity_id)s
            AND r.relationship_definition_keyname = '%(rdk)s'
            AND re.deleted IS NULL
            AND e.deleted IS NULL
            AND r.deleted IS NULL
        """  % {'entity_id': self.formula.entity_id, 'rdk': tokens[1]}

        if tokens[2] != '*':
            sql += """
                AND re.entity_definition_keyname = '%(edk)s'
            """  % {'edk': tokens[2]}

        if tokens[3] != 'id':
            sql += """
                AND p.deleted IS NULL
                AND pd.dataproperty = '%(pdk)s'
            """ % {'pdk': tokens[3]}

        # logging.debug(sql)

        # Prepare formula dependencies
        # There are {COUNT(self.child.folder.id)} folders called {self.child.folder.name}

        dependency['relationship_definition_keyname'] = tokens[1]
        if _entity == 'related_entity':
            dependency['reverse_relationship'] = 1

        if tokens[2] != '*':
            dependency['entity_definition_keyname'] = tokens[2]

        if tokens[3] != 'id':
            dependency['dataproperty'] = tokens[3]

        self.formula.dependencies.append(dependency)

        return self.db.query(sql)

    def parcheck(self):
        return True
        s = Stack()
        balanced = True
        index = 0
        parenstr = re.search('([()])', self.xpr).join()
        while index < len(parenstr) and balanced:
            symbol = parenstr[index]
            if symbol == "(":
                s.push(symbol)
            else:
                if s.isEmpty():
                    balanced = False
                else:
                    s.pop()

            index = index + 1

        if balanced and s.isEmpty():
            return True
        else:
            return False


class Stack:
    def __init__(self):
        self.stack = []
    def push(self, item):
        self.stack.append(item)
    def check(self, item):
        return item in self.stack
    def pop(self):
        return self.stack.pop()
    @property
    def isEmpty(self):
        return self.stack == []
    @property
    def size(self):
        return len(self.stack)


class Queue:
    def __init__(self):
        self.in_stack = []
        self.out_stack = []
    def push(self, item):
        self.in_stack.append(item)
    def check(self, item):
        return (item in self.in_stack or item in self.out_stack)
    def pop(self):
        if not self.out_stack:
            self.in_stack.reverse()
            self.out_stack = self.in_stack
            self.in_stack = []
        return self.out_stack.pop()
    @property
    def isEmpty(self):
        return self.in_stack == [] and self.out_stack == []
    @property
    def size(self):
        return len(self.in_stack) + len(self.out_stack)


def mdbg(matchobj):
    # mdbg() is for regex match object debugging.
    #   i.e: re.sub(r"([^{]*){([^{}]*)}|(.*?)$", mdbg, self.formula)(ha()a)
    for m in matchobj.groups():
        None
        logging.debug(m)


def sortableDateTime(s_date):
    formatted_date = '%(year)d%(month)02d%(day)02d%(hour)02d%(minute)02d%(second)02d' % {'year': s_date.year, 'month': s_date.month, 'day': s_date.day, 'hour': s_date.hour, 'minute': s_date.minute, 'second': s_date.second}
    logging.debug(formatted_date)
    return formatted_date


def sortableInteger(s_integer):
    return sortableDecimal(s_integer)


def sortableDecimal(s_decimal):
    logging.debug(s_decimal)
    formatted_decimal = '%016.4f' % s_decimal
    logging.debug(formatted_decimal)
    return formatted_decimal


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
