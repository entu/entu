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
from decimal import Decimal

from helper import *


class Entity():
    """
    Entity class.

    """
    __translation = None

    @property
    def __user_id(self):
        if not self.current_user:
            return None
        if not self.current_user.id:
            return None
        return self.current_user.id

    def __get_system_translation(self, field, entity_definition_keyname='', property_definition_keyname=''):
        if not self.__translation:
            self.__translation = {}
            for t in self.db.query('SELECT field, value, IFNULL(entity_definition_keyname, \'\') AS entity_definition_keyname, IFNULL(property_definition_keyname, \'\') AS property_definition_keyname FROM translation WHERE language = %s OR language IS NULL ORDER BY language;', self.get_user_locale().code):
                self.__translation['%s|%s|%s' % (t.entity_definition_keyname, t.property_definition_keyname, t.field)] = t.value
        return self.__translation.get('%s|%s|%s' % (entity_definition_keyname, property_definition_keyname, field), None)

    def create_entity(self, entity_definition_keyname, parent_entity_id=None):
        """
        Creates new Entity and returns its ID.

        """
        # logging.debug('creating %s under entity %s' % (entity_definition_keyname, parent_entity_id))
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
        entity_id = self.db.execute_lastrowid(sql, entity_definition_keyname, self.__user_id)

        if not parent_entity_id:
            return entity_id

        # Propagate sharing
        parent = self.db.get('SELECT sharing FROM entity WHERE id = %s LIMIT 1;', parent_entity_id)
        self.db.execute('UPDATE entity SET sharing = %s WHERE id = %s LIMIT 1;', parent.sharing, entity_id)

        # Insert child relationship and/or default parent child relationship
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
            AND r.is_deleted = 0
            AND r.entity_definition_keyname = %s
            UNION SELECT
                'child',
                %s,
                %s,
                %s,
                NOW();
        """
        # logging.debug(sql)
        self.db.execute(sql, entity_id, self.__user_id, entity_definition_keyname, parent_entity_id, entity_id, self.__user_id)

        # Insert or update "contains" information
        for row in self.db.query("SELECT entity_id FROM relationship r WHERE r.is_deleted = 0 AND r.relationship_definition_keyname = 'child' AND r.related_entity_id = %s" , entity_id):
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
            WHERE     r.is_deleted = 0
            AND       r.related_entity_id = %s
            AND       r.relationship_definition_keyname = 'child'
            AND       rr.is_deleted = 0
            AND       rr.relationship_definition_keyname IN ('viewer', 'expander', 'editor', 'owner');
        """
        # logging.debug(sql)
        self.db.execute(sql, entity_id, self.__user_id, entity_id)

        # set creator to owner
        self.set_rights(entity_id=entity_id, related_entity_id=self.__user_id, right='owner')

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
                value_reference,
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
                p.value_reference,
                p.value_file,
                p.value_counter,
                %s,
                NOW()
            FROM
                relationship AS r,
                property AS p
            WHERE p.property_definition_keyname = r.property_definition_keyname
            AND p.entity_id = %s
            AND r.relationship_definition_keyname = 'propagated-property'
            AND p.is_deleted = 0
            AND r.is_deleted = 0
            ;
        """
        # logging.debug(sql)
        self.db.execute(sql, entity_id, self.__user_id, parent_entity_id)

        return entity_id

    def duplicate_entity(self, entity_id, copies=1, skip_property_definition_keyname=None):
        if not entity_id:
            return

        if skip_property_definition_keyname:
            if type(skip_property_definition_keyname) is not list:
                skip_property_definition_keyname = [skip_property_definition_keyname]
            properties_sql = 'AND property_definition_keyname NOT IN (%s)' % ','.join(['\'%s\'' % x for x in map(str, skip_property_definition_keyname)])
        else:
            properties_sql = ''

        for x in range(int(copies)):
            new_entity_id = self.db.execute_lastrowid("""
                INSERT INTO entity (
                    definition_id,
                    entity_definition_keyname,
                    sharing,
                    created,
                    created_by
                ) SELECT
                    definition_id,
                    entity_definition_keyname,
                    sharing,
                    NOW(),
                    %s
                FROM entity
                WHERE id = %s;
            """ , self.__user_id, entity_id)
            self.db.execute("""
                INSERT INTO property (
                    definition_id,
                    property_definition_keyname,
                    entity_id,
                    ordinal,
                    language,
                    value_formula,
                    value_string,
                    value_text,
                    value_integer,
                    value_decimal,
                    value_boolean,
                    value_datetime,
                    value_entity,
                    value_reference,
                    value_file,
                    value_counter,
                    created,
                    created_by
                ) SELECT
                    definition_id,
                    property_definition_keyname,
                    %s,
                    ordinal,
                    language,
                    value_formula,
                    value_string,
                    value_text,
                    value_integer,
                    value_decimal,
                    value_boolean,
                    value_datetime,
                    value_entity,
                    value_reference,
                    value_file,
                    value_counter,
                    NOW(),
                    %s
                    FROM property
                    WHERE entity_id = %s
                    %s
                    AND is_deleted = 0;
            """ % (new_entity_id, self.__user_id, entity_id, properties_sql))
            self.db.execute("""
                INSERT INTO relationship (
                    relationship_definition_keyname,
                    entity_id,
                    related_entity_id,
                    created,
                    created_by
                ) SELECT
                    relationship_definition_keyname,
                    %s,
                    related_entity_id,
                    NOW(),
                    %s
                FROM relationship
                WHERE entity_id = %s
                AND relationship_definition_keyname IN ('viewer', 'expander', 'editor', 'owner')
                AND is_deleted = 0;
            """, new_entity_id, self.__user_id, entity_id)
            self.db.execute("""
                INSERT INTO relationship (
                    relationship_definition_keyname,
                    entity_id,
                    related_entity_id,
                    created,
                    created_by
                ) SELECT
                    relationship_definition_keyname,
                    entity_id,
                    %s,
                    NOW(),
                    %s
                FROM relationship
                WHERE related_entity_id = %s
                AND relationship_definition_keyname IN ('child', 'viewer', 'expander', 'editor', 'owner')
                AND is_deleted = 0;
            """, new_entity_id, self.__user_id, entity_id)

    def delete_entity(self, entity_id):
        for child_id in self.get_relatives(ids_only=True, entity_id=entity_id, relationship_definition_keyname='child'):
            self.delete_entity(child_id)

        self.db.execute('UPDATE entity SET deleted = NOW(), is_deleted = 1, deleted_by = %s WHERE id = %s;', self.__user_id, entity_id)

        # remove "contains" information
        self.db.execute('DELETE FROM dag_entity WHERE entity_id = %s OR related_entity_id = %s;', entity_id, entity_id)

    def set_property(self, entity_id=None, relationship_id=None, property_definition_keyname=None, value=None, old_property_id=None, uploaded_file=None):
        """
        Saves property value. Creates new one if old_property_id = None. Returns new_property_id.

        """
        if not entity_id:
            return

        # property_definition_keyname is preferred because it could change for existing property
        # logging.debug("Set property %s." % old_property_id)
        if old_property_id:
            definition = self.db.get('SELECT pd.datatype, pd.keyname, pd.formula, p.value_string, p.value_formula FROM property p LEFT JOIN property_definition pd ON pd.keyname = p.property_definition_keyname WHERE p.id = %s;', old_property_id)
            property_definition_keyname = definition.keyname
        elif property_definition_keyname:
            definition = self.db.get('SELECT datatype, formula FROM property_definition WHERE keyname = %s LIMIT 1;', property_definition_keyname)
        else:
            # logging.debug("Dont set property %s." % old_property_id)
            return

        # logging.debug(definition)

        if not definition:
            return

        # logging.debug(old_property_id)
        if old_property_id:
            # logging.debug(definition)
            if definition.formula == 1:
                try:
                    fval = ''.join([x for x in Formula(self.db, user_locale=self.get_user_locale(), created_by=self.__user_id, entity_id=entity_id, property_id=old_property_id, formula=definition.value_formula).evaluate()]).decode('utf-8')
                except Exception:
                    fval = ''.join([x.encode('utf-8') for x in Formula(self.db, user_locale=self.get_user_locale(), created_by=self.__user_id, entity_id=entity_id, property_id=old_property_id, formula=definition.value_formula).evaluate()]).decode('utf-8')
                # logging.error((fval, definition.value_string))
                if definition.value_string == fval:
                    return

            # logging.debug('UPDATE property SET deleted = NOW(), is_deleted = 1, deleted_by = %s WHERE id = %s;' % (self.__user_id, old_property_id) )
            self.db.execute('UPDATE property SET deleted = NOW(), is_deleted = 1, deleted_by = %s WHERE id = %s;', self.__user_id, old_property_id )

        # If no value, then property is deleted, return
        if not value:
            return

        new_property_id = self.db.execute_lastrowid('INSERT INTO property SET entity_id = %s, property_definition_keyname = %s, created = NOW(), created_by = %s;',
            entity_id,
            property_definition_keyname,
            self.__user_id
        )

        if definition.formula == 1:
            formula = Formula(self.db, user_locale=self.get_user_locale(), created_by=self.__user_id, entity_id=entity_id, property_id=new_property_id, formula=value)
            value = ''.join(formula.evaluate())

        if definition.datatype != 'file':
            value_string = value[:500]

        if definition.datatype in ['text', 'html']:
            field = 'value_text'
        elif definition.datatype == 'integer':
            field = 'value_integer'
        elif definition.datatype == 'decimal':
            field = 'value_decimal'
            value = value.replace(',', '.')
            value = re.sub(r'[^\.0-9:]', '', value)
            value_string = '%s'[:500] % (value)
        elif definition.datatype == 'date':
            field = 'value_datetime'
        elif definition.datatype == 'datetime':
            field = 'value_datetime'
        elif definition.datatype == 'reference':
            field = 'value_reference'
            value_string = self.__get_properties(value)[0]['displayname']
        elif definition.datatype == 'file':
            uploaded_file = value
            value = self.db.execute_lastrowid('INSERT INTO file SET filename = %s, filesize = %s, file = %s, is_link = %s, created_by = %s, created = NOW();', uploaded_file.get('filename', ''), len(uploaded_file.get('body', '')), uploaded_file.get('body', ''), uploaded_file.get('is_link', 0), self.__user_id)
            field = 'value_file'
            value_string = uploaded_file['filename'][:500]
        elif definition.datatype == 'boolean':
            field = 'value_boolean'
            value = 1 if value.lower() == 'true' else 0
        elif definition.datatype == 'counter':
            field = 'value_counter'
        else:
            field = 'value_string'
            value = value[:500]
            value_string = ''


        if value_string:
            # logging.debug('UPDATE property SET %s = %s, value_string = %s WHERE id = %s;' % (field, value, value_string, new_property_id) )
            self.db.execute('UPDATE property SET %s = %%s, value_string = %%s WHERE id = %%s;' % field, value, value_string, new_property_id )
        else:
            # logging.debug('UPDATE property SET %s = %s WHERE id = %s;' % (field, value, new_property_id) )
            self.db.execute('UPDATE property SET %s = %%s WHERE id = %%s;' % field, value, new_property_id )

        if definition.formula == 1:
            formula.save_property(new_property_id=new_property_id, old_property_id=old_property_id)

        self.db.execute('UPDATE entity SET changed = NOW(), changed_by = %s WHERE id = %s;',
            self.__user_id,
            entity_id,
        )

        return new_property_id

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
                    AND entity.id IN (SELECT entity_id FROM relationship WHERE related_entity_id = %(entity_id)s AND relationship_definition_keyname = 'child')
                    AND entity.is_deleted = 0
                    AND property.is_deleted = 0
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
                    AND entity.id IN (SELECT entity_id FROM relationship WHERE related_entity_id = %(entity_id)s AND relationship_definition_keyname = 'child')
                    AND entity.is_deleted = 0
                    AND property.is_deleted = 0
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
            AND property.entity_id IN (SELECT entity_id FROM relationship WHERE related_entity_id = %(entity_id)s AND relationship_definition_keyname = 'child')
            AND property_definition.datatype= 'counter'
            AND property_definition2.datatype = 'counter-value'
            AND relationship.relationship_definition_keyname = 'target-property'
            AND property_definition2.entity_definition_keyname = (SELECT entity_definition_keyname FROM entity WHERE id = %(entity_id)s LIMIT 1)
            AND relationship.is_deleted = 0
            AND property.is_deleted = 0
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
                AND property.entity_id IN (SELECT entity_id FROM relationship WHERE related_entity_id = %(entity_id)s AND relationship_definition_keyname = 'child')
                AND property_definition.datatype= 'counter'
                AND property_definition2.datatype = 'counter-value'
                AND relationship.relationship_definition_keyname = 'target-property'
                AND property_definition2.entity_definition_keyname = (SELECT entity_definition_keyname FROM entity WHERE id = %(entity_id)s LIMIT 1)
                AND counter.type = 'increment'
                AND relationship.is_deleted = 0
                AND property.is_deleted = 0
                ) X
            SET
                counter.value = counter.value + counter.increment,
                counter.changed_by = '%(user_id)s',
                counter.changed = NOW()
            WHERE counter.id = X.id;
        """ % {'entity_id': entity_id, 'user_id': self.__user_id}
        # logging.debug(sql)

        property_id = self.db.execute_lastrowid(sql)
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
                                deleted_by = %s,
                                deleted = NOW(),
                                is_deleted = 1
                            WHERE relationship_definition_keyname = '%s'
                            AND entity_id = %s
                            AND related_entity_id = %s;
                        """ % (self.__user_id, t, e, r)
                        # logging.debug(sql)
                        self.db.execute(sql)
                    elif update == True:
                        sql = """
                            UPDATE relationship SET
                                deleted_by = NULL,
                                deleted = NULL,
                                changed_by = %s,
                                changed = NOW()
                            WHERE relationship_definition_keyname = '%s'
                            AND entity_id = %s
                            AND related_entity_id = %s;
                        """ % (self.__user_id, t, e, r)
                        # logging.debug(sql)
                        old = self.db.execute_rowcount(sql)
                        if not old:
                            sql = """
                                INSERT INTO relationship SET
                                    relationship_definition_keyname = '%s',
                                    entity_id = %s,
                                    related_entity_id = %s,
                                    created_by = %s,
                                    created = NOW();
                            """ % (t, e, r, self.__user_id)
                            # logging.debug(sql)
                            self.db.execute(sql)
                    else:
                        sql = """
                            SELECT id
                            FROM relationship
                            WHERE relationship_definition_keyname = '%s'
                            AND entity_id = %s
                            AND related_entity_id = %s
                            AND is_deleted = 0;
                        """ % (t, e, r)
                        old = self.db.get(sql)
                        # logging.debug(sql)
                        if not old:
                            sql = """
                                INSERT INTO relationship SET
                                    relationship_definition_keyname = '%s',
                                    entity_id = %s,
                                    related_entity_id = %s,
                                    created_by = %s,
                                    created = NOW();
                            """ % (t, e, r, self.__user_id)
                            # logging.debug(sql)
                            self.db.execute(sql)

    def get_rights(self, entity_id):
        if not entity_id:
            return

        rights = {}
        for right in ['viewer', 'expander', 'editor', 'owner']:
            sql = """
                SELECT related_entity_id
                FROM relationship
                WHERE is_deleted = 0
                AND relationship_definition_keyname = %s
                AND entity_id = %s
            """

            relationship = self.db.query(sql, right, entity_id)
            if not relationship:
                continue

            ids = [x.related_entity_id for x in relationship if x.related_entity_id]
            if ids:
                entities = self.__get_properties(entity_id=ids, full_definition=False, only_public=False)
                if entities:
                    rights[right] = entities

        return rights

    def set_rights(self, entity_id, related_entity_id, right=None):
        if not entity_id or not related_entity_id:
            return

        if type(entity_id) is not list:
            entity_id = [entity_id]

        if type(related_entity_id) is not list:
            related_entity_id = [related_entity_id]

        sql = """
            UPDATE relationship SET
                deleted = NOW(),
                is_deleted = 1,
                deleted_by = %s
            WHERE is_deleted = 0
            AND relationship_definition_keyname IN ('viewer', 'expander', 'editor', 'owner')
            AND entity_id IN (%s)
            AND related_entity_id IN (%s);
        """ % (self.__user_id, ','.join(map(str, entity_id)), ','.join(map(str, related_entity_id)))
        self.db.execute(sql)

        if right in ['viewer', 'expander', 'editor', 'owner']:
            for e in entity_id:
                for re in related_entity_id:
                    self.db.execute('INSERT INTO relationship SET relationship_definition_keyname = %s, entity_id = %s, related_entity_id = %s, created = NOW(), created_by = %s;', right, int(e), int(re), self.__user_id)

    def set_sharing(self, entity_id, sharing):
        if not entity_id or not sharing:
            return

        if type(entity_id) is not list:
            entity_id = [entity_id]

        sql = """
            UPDATE entity SET
                sharing = %%s,
                changed = NOW(),
                changed_by = %%s
            WHERE id IN (%s);
        """ % ','.join(map(str, entity_id))

        self.db.execute(sql, sharing, self.__user_id)

    def get_entities(self, ids_only=False, entity_id=None, search=None, entity_definition_keyname=None, dataproperty=None, limit=None, full_definition=False, only_public=False):
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

        if limit == 1 and len(entities) > 0:
            return entities[0]

        return entities

    def __get_id_list(self, entity_id=None, search=None, entity_definition_keyname=None, limit=None, only_public=False):
        """
        Get list of Entity IDs. entity_id, entity_definition_keyname and user_id can be single ID or list of IDs.

        """

        select_parts = ['e.id AS id']
        join_parts = []
        where_parts = ['e.is_deleted = 0']
        sql_parts = []

        if search != None:
            i = 0
            for s in search.split(' ')[:5]:
                if not s:
                    continue
                i += 1
                join_parts.append('RIGHT JOIN property AS p%(idx)i ON p%(idx)i.entity_id = e.id RIGHT JOIN property_definition AS ppd%(idx)i ON ppd%(idx)i.keyname = p%(idx)i.property_definition_keyname AND ppd%(idx)i.search = 1' % {'idx': i})
                if not self.__user_id or only_public == True:
                    join_parts.append('LEFT JOIN property_definition AS pd%i ON pd%i.keyname = p%i.property_definition_keyname' % (i, i, i))

                where_parts.append('p%i.value_string LIKE \'%%%%%s%%%%\'' % (i, s))
                where_parts.append('p%i.is_deleted = 0' % i)

        if entity_definition_keyname != None:
            if type(entity_definition_keyname) is not list:
                entity_definition_keyname = [entity_definition_keyname]
            where_parts.append('e.entity_definition_keyname IN (%s)' % ','.join(['\'%s\'' % x for x in map(str, entity_definition_keyname)]))

        if entity_id != None:
            if type(entity_id) is not list:
                entity_id = [entity_id]
            where_parts.append('e.id IN (%s)' % ','.join(map(str, entity_id)))

        if self.__user_id and only_public == False:
            where_parts.append('r.is_deleted = 0')
            join_parts.append('RIGHT JOIN relationship AS r  ON r.entity_id  = e.id')
            where_parts.append('(r.related_entity_id = %s AND r.relationship_definition_keyname IN (\'viewer\', \'expander\', \'editor\', \'owner\') OR e.sharing IN (\'domain\', \'public\'))' % self.__user_id)
        else:
            where_parts.append('e.sharing = \'public\'')
            i = 0
            if search != None:
                for s in search.split(' '):
                    i += 1
                    where_parts.append('pd%i.public = 1' % i)

        if len(select_parts) > 0:
            sql_parts.append('SELECT DISTINCT %s' % ', '.join(select_parts))

        sql_parts.append(' FROM entity AS e')

        if len(join_parts) > 0:
            sql_parts.append(' %s' %  ' '.join(join_parts))

        if len(where_parts) > 0:
            sql_parts.append(' WHERE %s' % ' AND '.join(where_parts))

        if limit:
            limit = ' LIMIT %s' % limit
        else:
            limit = ''

        sql_parts.append(' ORDER BY e.sort, e.created DESC%s;' % limit)

        sql = ''.join(sql_parts)
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
            AND p.is_deleted = 0
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

            if self.__user_id and only_public == False:
                rights_select = 'relationship.relationship_definition_keyname'
                rights_join = 'LEFT JOIN relationship ON relationship.entity_id = entity.id AND relationship.is_deleted = 0 AND relationship.related_entity_id = %s AND relationship.relationship_definition_keyname IN (\'viewer\', \'expander\', \'editor\', \'owner\')' % self.__user_id
                public = ''
            else:
                rights_select = 'FALSE'
                rights_join = ''
                public = 'AND entity.sharing = \'public\' AND property_definition.public = 1'

            datapropertysql = ''
            if dataproperty:
                if type(dataproperty) is not list:
                    dataproperty = [dataproperty]
                datapropertysql = 'AND property_definition.dataproperty IN (%s)' % ','.join(['\'%s\'' % x for x in dataproperty])

            sql = """
                SELECT
                    entity_definition.keyname                       AS entity_definition_keyname,
                    entity.id                                       AS entity_id,
                    entity.created                                  AS entity_created,
                    entity.changed                                  AS entity_changed,
                    entity.sharing                                  AS entity_sharing,
                    %(rights_select)s                               AS entity_right,
                    entity.sort                                     AS entity_sort_value,
                    property_definition.keyname                     AS property_keyname,
                    property_definition.ordinal                     AS property_ordinal,
                    property_definition.formula                     AS property_formula,
                    property_definition.executable                  AS property_executable,
                    property_definition.datatype                    AS property_datatype,
                    property_definition.dataproperty                AS property_dataproperty,
                    property_definition.mandatory                   AS property_mandatory,
                    property_definition.multilingual                AS property_multilingual,
                    property_definition.multiplicity                AS property_multiplicity,
                    property_definition.public                      AS property_public,
                    property_definition.readonly                    AS property_readonly,
                    property_definition.visible                     AS property_visible,
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
                    entity %(rights_join)s,
                    entity_definition,
                    property,
                    property_definition
                WHERE property.entity_id = entity.id
                AND entity_definition.keyname = entity.entity_definition_keyname
                AND property_definition.keyname = property.property_definition_keyname
                AND entity_definition.keyname = property_definition.entity_definition_keyname
                AND (property.language = '%(language)s' OR property.language IS NULL)
                AND entity.id IN (%(idlist)s)
                AND entity.is_deleted = 0
                AND property.is_deleted = 0
                %(public)s
                %(datapropertysql)s
                ORDER BY
                    entity_definition.keyname,
                    entity.created DESC
            """ % {'language': self.get_user_locale().code, 'public': public, 'idlist': ','.join(map(str, entity_id)), 'datapropertysql': datapropertysql, 'rights_select': rights_select, 'rights_join': rights_join}
            # logging.debug(sql)

            items = {}
            for row in self.db.query(sql):
                if row.entity_sharing == 'private' and not row.entity_right:
                    continue
                if row.entity_sharing in ['domain', 'public'] and row.entity_right not in ['viewer', 'expander', 'editor', 'owner'] and row.property_public != 1:
                    continue

                #Entity
                items.setdefault('item_%s' % row.entity_id, {})['definition_keyname'] = row.entity_definition_keyname
                items.setdefault('item_%s' % row.entity_id, {})['id'] = row.entity_id
                items.setdefault('item_%s' % row.entity_id, {})['label'] = self.__get_system_translation(field='label', entity_definition_keyname=row.entity_definition_keyname)
                items.setdefault('item_%s' % row.entity_id, {})['label_plural'] = self.__get_system_translation(field='label_plural', entity_definition_keyname=row.entity_definition_keyname)
                items.setdefault('item_%s' % row.entity_id, {})['description'] = self.__get_system_translation(field='description', entity_definition_keyname=row.entity_definition_keyname)
                items.setdefault('item_%s' % row.entity_id, {})['sort'] = self.__get_system_translation(field='sort', entity_definition_keyname=row.entity_definition_keyname)
                items.setdefault('item_%s' % row.entity_id, {})['sort_value'] = row.entity_sort_value
                items.setdefault('item_%s' % row.entity_id, {})['created'] = row.entity_created
                items.setdefault('item_%s' % row.entity_id, {})['changed'] = row.entity_changed
                items.setdefault('item_%s' % row.entity_id, {})['displayname'] = self.__get_system_translation(field='displayname', entity_definition_keyname=row.entity_definition_keyname)
                items.setdefault('item_%s' % row.entity_id, {})['displayinfo'] = self.__get_system_translation(field='displayinfo', entity_definition_keyname=row.entity_definition_keyname)
                items.setdefault('item_%s' % row.entity_id, {})['displaytable'] = self.__get_system_translation(field='displaytable', entity_definition_keyname=row.entity_definition_keyname)
                items.setdefault('item_%s' % row.entity_id, {})['file_count'] = 0
                items.setdefault('item_%s' % row.entity_id, {})['sharing'] = row.entity_sharing
                items.setdefault('item_%s' % row.entity_id, {})['right'] = row.entity_right
                items.setdefault('item_%s' % row.entity_id, {})['ordinal'] = row.entity_created if row.entity_created else datetime.datetime.now()

                #Property
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['keyname'] = row.property_keyname
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['fieldset'] = self.__get_system_translation(field='fieldset', property_definition_keyname=row.property_keyname)
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['label'] = self.__get_system_translation(field='label', property_definition_keyname=row.property_keyname)
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['label_plural'] = self.__get_system_translation(field='label_plural', property_definition_keyname=row.property_keyname)
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['description'] = self.__get_system_translation(field='description', property_definition_keyname=row.property_keyname)
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['datatype'] = row.property_datatype
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['dataproperty'] = row.property_dataproperty
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['mandatory'] = bool(row.property_mandatory)
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['multilingual'] = bool(row.property_multilingual)
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['multiplicity'] = row.property_multiplicity
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['ordinal'] = row.property_ordinal
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['formula'] = bool(row.property_formula)
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['executable'] = bool(row.property_executable)
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['public'] = bool(row.property_public)
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['readonly'] = bool(row.property_readonly)
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['visible'] = bool(row.property_visible)

                #X properties
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {})['x_created'] = {
                    'keyname' : 'x_created',
                    'fieldset' : 'X',
                    'label' : self.get_user_locale().translate('created'),
                    'label_plural' : self.get_user_locale().translate('created'),
                    'description' : '',
                    'datatype': 'datetime',
                    'dataproperty' : 'x_created',
                    'mandatory' : False,
                    'multilingual' : False,
                    'multiplicity' : 1,
                    'ordinal' : 100000,
                    'formula' : False,
                    'executable' : False,
                    'public' : False,
                    'readonly' : True,
                    'visible' : True,
                    'values': {'value_0': {
                        'id': 0,
                        'ordinal': 0,
                        'value': formatDatetime(row.entity_created) if row.entity_created else '',
                        'db_value': row.entity_created if row.entity_created else None
                    }}
                }

                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {})['x_changed'] = {
                    'keyname' : 'x_changed',
                    'fieldset' : 'X',
                    'label' : self.get_user_locale().translate('changed'),
                    'label_plural' : self.get_user_locale().translate('changed'),
                    'description' : '',
                    'datatype': 'datetime',
                    'dataproperty' : 'x_changed',
                    'mandatory' : False,
                    'multilingual' : False,
                    'multiplicity' : 1,
                    'ordinal' : 100001,
                    'formula' : False,
                    'executable' : False,
                    'public' : False,
                    'readonly' : True,
                    'visible' : True,
                    'values': {'value_0': {
                        'id': 0,
                        'ordinal': 0,
                        'value': formatDatetime(row.entity_changed) if row.entity_changed else '',
                        'db_value': row.entity_created if row.entity_changed else None
                    }}
                }

                #Value
                if row.property_datatype in ['string', 'select']:
                    db_value = row.value_string if row.value_string else ''
                    value = row.value_string if row.value_string else ''
                elif row.property_datatype in ['text', 'html']:
                    db_value = row.value_text if row.value_text else ''
                    value = row.value_text if row.value_text else ''
                elif row.property_datatype == 'integer':
                    db_value = row.value_integer
                    value = row.value_integer if row.value_integer else ''
                elif row.property_datatype == 'decimal':
                    db_value = row.value_decimal
                    value = '%.2f' % row.value_decimal if row.value_decimal else ''
                elif row.property_datatype == 'date':
                    db_value = row.value_datetime
                    value = formatDatetime(row.value_datetime, '%(day)02d.%(month)02d.%(year)d')
                elif row.property_datatype == 'datetime':
                    db_value = row.value_datetime
                    value = formatDatetime(row.value_datetime) if row.value_datetime else ''
                elif row.property_datatype == 'reference':
                    value = ''
                    if row.value_reference:
                        if row.value_reference == row.entity_id:
                            value = 'self'
                        else:
                            reference = self.__get_properties(entity_id=row.value_reference)
                            if reference:
                                value = reference[0].get('displayname')
                    db_value = row.value_reference
                elif row.property_datatype == 'file':
                    db_value = row.value_file
                    blobstore = self.db.get('SELECT id, filename, filesize FROM file WHERE id=%s LIMIT 1', row.value_file)
                    value = blobstore.filename if blobstore else ''
                    items.setdefault('item_%s' % row.entity_id, {})['file_count'] += 1
                elif row.property_datatype == 'boolean':
                    db_value = row.value_boolean
                    value = self.get_user_locale().translate('boolean_true') if row.value_boolean == 1 else self.get_user_locale().translate('boolean_false')
                elif row.property_datatype == 'counter':
                    counter = self.db.get('SELECT %(language)s_label AS label FROM counter WHERE id=%(id)s LIMIT 1' % {'language': self.get_user_locale().code, 'id': row.value_counter})
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
                    self.set_property(entity_id = row.entity_id, old_property_id = row.value_id, value = row.value_formula)
                    # logging.debug(row.value_id)
                    # logging.debug(row.value_formula)
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
                items[key]['displaypicture'] = self.__get_picture_url(value['id'], value['definition_keyname'])

            items[key]['completed'] = True
            for d in self.get_definition(entity_definition_keyname=value['definition_keyname']):
                if not value.get('id', None):
                    items[key]['displayname'] = d['entity_label']
                items[key].setdefault('properties', {}).setdefault('%s' % d['property_dataproperty'], {})['keyname'] = d['property_keyname']
                items[key].setdefault('properties', {}).setdefault('%s' % d['property_dataproperty'], {})['fieldset'] = d['property_fieldset']
                items[key].setdefault('properties', {}).setdefault('%s' % d['property_dataproperty'], {})['label'] = d['property_label']
                items[key].setdefault('properties', {}).setdefault('%s' % d['property_dataproperty'], {})['label_plural'] = d['property_label_plural']
                items[key].setdefault('properties', {}).setdefault('%s' % d['property_dataproperty'], {})['description'] = d['property_description']
                items[key].setdefault('properties', {}).setdefault('%s' % d['property_dataproperty'], {})['datatype'] = d['property_datatype']
                items[key].setdefault('properties', {}).setdefault('%s' % d['property_dataproperty'], {})['dataproperty'] = d['property_dataproperty']
                items[key].setdefault('properties', {}).setdefault('%s' % d['property_dataproperty'], {})['mandatory'] = d['property_mandatory']
                items[key].setdefault('properties', {}).setdefault('%s' % d['property_dataproperty'], {})['multilingual'] = d['property_multilingual']
                items[key].setdefault('properties', {}).setdefault('%s' % d['property_dataproperty'], {})['multiplicity'] = d['property_multiplicity']
                items[key].setdefault('properties', {}).setdefault('%s' % d['property_dataproperty'], {})['ordinal'] = d['property_ordinal']
                items[key].setdefault('properties', {}).setdefault('%s' % d['property_dataproperty'], {})['public'] = d['property_public']
                items[key].setdefault('properties', {}).setdefault('%s' % d['property_dataproperty'], {})['readonly'] = d['property_readonly']
                items[key].setdefault('properties', {}).setdefault('%s' % d['property_dataproperty'], {})['visible'] = d['property_visible']

                if d['property_mandatory'] and len(value.get('properties', {}).get('%s' % d['property_dataproperty'], {}).get('values', {}).values()) < 1:
                    items[key]['completed'] = False

                if full_definition:
                    if not d['property_multiplicity'] or d['property_multiplicity'] > len(value.get('properties', {}).get('%s' % d['property_dataproperty'], {}).get('values', {}).values()):
                        items[key].setdefault('properties', {}).setdefault('%s' % d['property_dataproperty'], {}).setdefault('values', {})['value_new'] = {'id': '', 'ordinal': 'X', 'value': '', 'db_value': ''}
                    if not d['property_multiplicity'] or d['property_multiplicity'] > len(value.get('properties', {}).get('%s' % d['property_dataproperty'], {}).get('values', {}).values()):
                        items[key].setdefault('properties', {}).setdefault('%s' % d['property_dataproperty'], {})['can_add_new'] = True
                    else:
                        items[key].setdefault('properties', {}).setdefault('%s' % d['property_dataproperty'], {})['can_add_new'] = False

                    if d['property_classifier_id'] and d['property_datatype'] != 'reference':
                        for c in self.get_entities(entity_definition_keyname=d['property_classifier_id'], only_public=True):
                            if c.get('id', None):
                                items[key].setdefault('properties', {}).setdefault('%s' % d['property_dataproperty'], {}).setdefault('select', []).append({'id': c.get('id', ''), 'label': c.get('displayname', '')})

            for p_key, p_value in value.get('properties', {}).iteritems():
                if p_value.get('values'):
                    items[key]['properties'][p_key]['values'] = sorted(p_value.get('values', {}).values(), key=itemgetter('ordinal'))
                if p_value['datatype'] == 'reference':
                    reference_definition = self.db.get('SELECT classifying_entity_definition_keyname FROM property_definition WHERE keyname = %s LIMIT 1;', p_value['keyname'])
                    if reference_definition:
                        if reference_definition.classifying_entity_definition_keyname:
                            items[key]['properties'][p_key]['reference_definition'] = reference_definition.classifying_entity_definition_keyname

        return items.values()

    def __get_displayfields(self, entity_dict):
        """
        Returns Entity displayname, displayinfo, displaytable fields.

        """
        result = {}
        for displayfield in ['displayname', 'displayinfo', 'displaytable', 'sort']:
            result[displayfield] = entity_dict.get(displayfield, '') if entity_dict.get(displayfield, '') else None
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

        result['displaytable_labels'] = self.__get_system_translation(field='displaytableheader', entity_definition_keyname=entity_dict.get('definition_keyname'))
        if not result['displaytable_labels']:
            result['displaytable_labels'] = entity_dict.get('displaytable', '') if entity_dict.get('displaytable', '') else None
            for data_property in findTags(entity_dict.get('displaytable', ''), '@', '@'):
                result['displaytable_labels'] = result['displaytable_labels'].replace('@%s@' % data_property, entity_dict.get('properties', {}).get(data_property, {}).get('label', ''))

        result['displaytable'] = result['displaytable'].split('|') if result['displaytable'] else None
        result['displaytable_labels'] = result['displaytable_labels'].split('|') if result['displaytable_labels'] else None

        if entity_dict.get('id', None) and entity_dict.get('sort_value', None) != result['sort']:
            self.db.execute('UPDATE entity SET sort = LEFT(%s, 100) WHERE id = %s', result['sort'], entity_dict.get('id'))

        return result

    def __get_picture_url(self, entity_id, entity_definition_keyname):
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
            AND property.is_deleted = 0
            LIMIT 1;
        """
        f = self.db.get(sql, entity_id)
        if f:
            return '/entity/file-%s' % f.id
        elif entity_definition_keyname in ['audiovideo', 'book', 'methodical', 'periodical', 'textbook', 'workbook']:
            return '/photo-by-isbn?entity=%s' % entity_id
        elif entity_definition_keyname == 'person':
            return 'https://secure.gravatar.com/avatar/%s?d=wavatar&s=150' % (hashlib.md5(str(entity_id)).hexdigest())
        else:
            return 'https://secure.gravatar.com/avatar/%s?d=identicon&s=150' % (hashlib.md5(str(entity_id)).hexdigest())


    def get_definition(self, entity_definition_keyname):
        """
        Returns Entity definition (with property definitions).

        """
        if not entity_definition_keyname:
            return

        if type(entity_definition_keyname) is not list:
            entity_definition_keyname = [entity_definition_keyname]

        sql = """
            SELECT
                entity_definition.keyname AS entity_definition_keyname,
                property_definition.keyname AS property_keyname,
                property_definition.datatype AS property_datatype,
                property_definition.dataproperty AS property_dataproperty,
                property_definition.mandatory AS property_mandatory,
                property_definition.multilingual AS property_multilingual,
                property_definition.multiplicity AS property_multiplicity,
                property_definition.ordinal AS property_ordinal,
                property_definition.public AS property_public,
                property_definition.readonly AS property_readonly,
                property_definition.visible AS property_visible,
                property_definition.classifying_entity_definition_keyname AS property_classifier_id
            FROM
                entity_definition,
                property_definition
            WHERE entity_definition.keyname = property_definition.entity_definition_keyname
            AND entity_definition.keyname IN (%s)
        """ % ','.join(['\'%s\'' % x for x in map(str, entity_definition_keyname)])
        # logging.debug(sql)

        defs = []
        for r in self.db.query(sql):
            defs.append({
                'entity_definition_keyname': r.entity_definition_keyname,
                'entity_label': self.__get_system_translation(field='label', entity_definition_keyname=r.entity_definition_keyname),
                'entity_label_plural': self.__get_system_translation(field='label_plural', entity_definition_keyname=r.entity_definition_keyname),
                'entity_description': self.__get_system_translation(field='description', entity_definition_keyname=r.entity_definition_keyname),
                'entity_displayname': self.__get_system_translation(field='displayname', entity_definition_keyname=r.entity_definition_keyname),
                'entity_displayinfo': self.__get_system_translation(field='displayinfo', entity_definition_keyname=r.entity_definition_keyname),
                'entity_displaytable': self.__get_system_translation(field='displaytable', entity_definition_keyname=r.entity_definition_keyname),
                'property_keyname': r.property_keyname,
                'property_fieldset': self.__get_system_translation(field='fieldset', property_definition_keyname=r.property_keyname),
                'property_label': self.__get_system_translation(field='label', property_definition_keyname=r.property_keyname),
                'property_label_plural': self.__get_system_translation(field='label_plural', property_definition_keyname=r.property_keyname),
                'property_description': self.__get_system_translation(field='description', property_definition_keyname=r.property_keyname),
                'property_datatype': r.property_datatype,
                'property_dataproperty': r.property_dataproperty,
                'property_mandatory': bool(r.property_mandatory),
                'property_multilingual': bool(r.property_multilingual),
                'property_multiplicity': r.property_multiplicity,
                'property_ordinal': r.property_ordinal,
                'property_public': bool(r.property_public),
                'property_readonly': bool(r.property_readonly),
                'property_visible': bool(r.property_visible),
                'property_classifier_id': r.property_classifier_id,
            })

        return defs

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
                open_after_add,
                ordinal,
                actions_add
            FROM
                entity_definition
            WHERE keyname IN (%s);
        """  % ','.join(['\'%s\'' % x for x in map(str, entity_definition_keyname)])
        # logging.debug(sql)

        defs = []
        for d in self.db.query(sql):
            defs.append({
                'keyname': d.keyname,
                'label': self.__get_system_translation(field='label', entity_definition_keyname=d.keyname),
                'label_plural': self.__get_system_translation(field='label_plural', entity_definition_keyname=d.keyname),
                'description': self.__get_system_translation(field='description', entity_definition_keyname=d.keyname),
                'menugroup': self.__get_system_translation(field='menu', entity_definition_keyname=d.keyname),
                'open_after_add': d.open_after_add,
                'ordinal': d.ordinal,
                'actions_add': d.actions_add
            })

        return defs


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

        unionsql = ''

        if reverse_relation == True:
            sql = """
                SELECT DISTINCT
                    r.id AS relationship_id,
                    r.entity_id AS id,
                    e.sort,
                    e.created
                FROM
                    entity AS e,
                    relationship AS r,
                    relationship AS rights
                WHERE r.entity_id = e.id
                AND rights.entity_id = e.id
                AND r.is_deleted = 0
                AND rights.is_deleted = 0
                AND e.is_deleted = 0
            """
        else:
            sql = """
                SELECT DISTINCT
                    r.id AS relationship_id,
                    r.related_entity_id AS id,
                    e.sort,
                    e.created
                FROM
                    entity AS e,
                    relationship AS r,
                    relationship AS rights
                WHERE r.related_entity_id = e.id
                AND rights.entity_id = e.id
                AND r.is_deleted = 0
                AND rights.is_deleted = 0
                AND e.is_deleted = 0
            """
            if not ids_only:
                unionsql = """
                    UNION SELECT DISTINCT
                        NULL AS relationship_id,
                        up.entity_id AS id,
                        ue.sort,
                        ue.created
                    FROM
                        property up,
                        entity ue,
                        relationship AS urights
                    WHERE ue.id = up.entity_id
                    AND urights.entity_id = ue.id
                    AND up.is_deleted = 0
                    AND ue.is_deleted = 0
                    AND urights.is_deleted = 0
                """

        if entity_id:
            sql += ' AND r.entity_id IN (%s)' % ','.join(map(str, entity_id))

        if related_entity_id:
            sql += ' AND r.related_entity_id IN (%s)' % ','.join(map(str, related_entity_id))

        if self.__user_id and only_public == False:
            sql += ' AND (rights.related_entity_id = %s AND rights.relationship_definition_keyname IN (\'viewer\', \'expander\', \'editor\', \'owner\') OR e.sharing  IN (\'domain\', \'public\'))' % self.__user_id
        else:
            sql += ' AND e.sharing = \'public\''

        if relationship_definition_keyname:
            sql += ' AND r.relationship_definition_keyname IN (%s)' % ','.join(['\'%s\'' % x for x in relationship_definition_keyname])

        if entity_definition_keyname:
            sql += ' AND e.entity_definition_keyname IN (%s)' % ','.join(['\'%s\'' % x for x in entity_definition_keyname])

        if unionsql:
            sql += unionsql

            if entity_id:
                sql += ' AND up.value_reference IN (%s)' % ','.join(map(str, entity_id))

            if self.__user_id and only_public == False:
                sql += ' AND (urights.related_entity_id = %s AND urights.relationship_definition_keyname IN (\'viewer\', \'expander\', \'editor\', \'owner\') OR ue.sharing  IN (\'domain\', \'public\'))' % self.__user_id
            else:
                sql += ' AND ue.sharing = \'public\''

            if entity_definition_keyname:
                sql += ' AND ue.entity_definition_keyname IN (%s)' % ','.join(['\'%s\'' % x for x in entity_definition_keyname])

        sql += ' ORDER BY sort, created DESC'

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

        if self.__user_id:
            public = ''
        else:
            public = 'AND pd.public = 1'

        sql = """
            SELECT
                f.id,
                f.created,
                f.file,
                f.filename,
                f.is_link
            FROM
                file AS f,
                property AS p,
                property_definition AS pd
            WHERE p.value_file = f.id
            AND pd.keyname = p.property_definition_keyname
            AND f.id IN (%(file_id)s)
            %(public)s
            AND p.is_deleted = 0
            """ % {'file_id': ','.join(map(str, file_id)), 'public': public}
        # logging.debug(sql)

        return self.db.query(sql)

    def get_allowed_childs(self, entity_id):
        """
        Returns allowed child definitions.

        """

        if not self.db.get('SELECT id FROM relationship WHERE relationship_definition_keyname iN (\'expander\', \'owner\') AND entity_id = %s AND related_entity_id = %s LIMIT 1;', entity_id, self.__user_id):
            return []

        sql = """
            SELECT DISTINCT
                entity_definition.keyname
            FROM
                relationship
                LEFT JOIN entity_definition ON relationship.related_entity_definition_keyname = entity_definition.keyname
            WHERE relationship.relationship_definition_keyname = 'allowed-child'
            AND relationship.entity_id = %s
            AND relationship.is_deleted = 0
            ORDER BY entity_definition.keyname
        """  % entity_id
        # logging.debug(sql)
        result = self.db.query(sql)

        if not result:
            sql = """
                SELECT DISTINCT
                    entity_definition.keyname
                FROM
                    entity_definition,
                    relationship
                WHERE relationship.related_entity_definition_keyname = entity_definition.keyname
                AND relationship.relationship_definition_keyname = 'allowed-child'
                AND relationship.entity_definition_keyname = (SELECT entity_definition_keyname FROM entity WHERE id = %s LIMIT 1)
                AND relationship.is_deleted = 0
            """  % entity_id
            # logging.debug(sql)
            result = self.db.query(sql)

        defs = []
        for d in self.db.query(sql):
            defs.append({
                'keyname': d.keyname,
                'label': self.__get_system_translation(field='label', entity_definition_keyname=d.keyname),
                'label_plural': self.__get_system_translation(field='label_plural', entity_definition_keyname=d.keyname),
                'description': self.__get_system_translation(field='description', entity_definition_keyname=d.keyname),
                'menugroup': self.__get_system_translation(field='menu', entity_definition_keyname=d.keyname),
            })

        return defs

    def get_allowed_parents(self, entity_id):
        """
        Returns allowed parent definitions.

        """

        sql = """
            SELECT DISTINCT IF(entity_id, (SELECT entity_definition_keyname FROM entity WHERE id = relationship.entity_id LIMIT 1), entity_definition_keyname) AS keyname
            FROM relationship
            WHERE relationship_definition_keyname = 'allowed-child'
            AND related_entity_definition_keyname = (SELECT entity_definition_keyname FROM entity WHERE id = %s LIMIT 1)
            AND is_deleted = 0;
        """  % entity_id
        # logging.debug(sql)
        result = self.db.query(sql)

        defs = []
        for d in self.db.query(sql):
            defs.append({
                'keyname': d.keyname,
                'label': self.__get_system_translation(field='label', entity_definition_keyname=d.keyname),
                'label_plural': self.__get_system_translation(field='label_plural', entity_definition_keyname=d.keyname),
                'description': self.__get_system_translation(field='description', entity_definition_keyname=d.keyname),
                'menugroup': self.__get_system_translation(field='menu', entity_definition_keyname=d.keyname),
            })

        return defs

    def get_definitions_with_optional_parent(self, entity_definition_keyname):
        """
        Returns allowed entity definitions what have default parent.

        """
        if not entity_definition_keyname:
            return {}

        if entity_definition_keyname:
            if type(entity_definition_keyname) is not list:
                entity_definition_keyname = [entity_definition_keyname]

        sql = """
            SELECT DISTINCT
                entity_definition.keyname,
                relationship.related_entity_id
            FROM
                entity_definition,
                relationship,
                relationship AS rights
            WHERE relationship.entity_definition_keyname = entity_definition.keyname
            AND rights.entity_id = relationship.related_entity_id
            AND relationship.relationship_definition_keyname = 'optional-parent'
            AND rights.relationship_definition_keyname iN ('expander', 'editor', 'owner')
            AND rights.related_entity_id = %s
            AND rights.is_deleted = 0
            AND entity_definition.keyname IN (%s)
            AND relationship.is_deleted = 0
        """  % (self.__user_id, ','.join(['\'%s\'' % x for x in map(str, entity_definition_keyname)]))
        # logging.debug(sql)

        defs = []
        for d in self.db.query(sql):
            related_entity = self.get_entities(entity_id=d.related_entity_id, limit=1)
            defs.append({
                'keyname': d.keyname,
                'label': self.__get_system_translation(field='label', entity_definition_keyname=d.keyname),
                'label_plural': self.__get_system_translation(field='label_plural', entity_definition_keyname=d.keyname),
                'description': self.__get_system_translation(field='description', entity_definition_keyname=d.keyname),
                'menugroup': self.__get_system_translation(field='menu', entity_definition_keyname=d.keyname),
                'related_entity_id': d.related_entity_id,
                'related_entity_label': related_entity.get('displayname') if related_entity else '',
            })

        return defs

    def get_public_paths(self):
        """
        Returns public paths with labels

        """

        paths = {}
        for i in self.db.query('SELECT DISTINCT keyname, public_path FROM entity_definition WHERE public_path IS NOT NULL ORDER BY public_path;'):
            paths[i.public_path] = self.__get_system_translation(field='public', entity_definition_keyname=i.keyname)
        return paths

    def get_menu(self):
        """
        Returns user menu.

        """

        sql = """
            SELECT DISTINCT
                entity_definition.keyname
            FROM
                entity_definition,
                entity,
                relationship
            WHERE entity.entity_definition_keyname = entity_definition.keyname
            AND relationship.entity_id = entity.id
            AND ((relationship.relationship_definition_keyname IN ('viewer', 'expander', 'editor', 'owner') AND relationship.is_deleted = 0 AND relationship.related_entity_id = %s) OR entity.sharing IN ('domain', 'public'))
            AND entity.is_deleted = 0

        """ % self.__user_id
        # logging.debug(sql)

        menu = {}
        for m in self.db.query(sql):
            group = self.__get_system_translation(field='menu', entity_definition_keyname=m.keyname)
            if not group:
                continue
            menu.setdefault(group, {})['label'] = group
            menu.setdefault(group, {}).setdefault('items', []).append({'keyname': m.keyname, 'title': self.__get_system_translation(field='label_plural', entity_definition_keyname=m.keyname)})

        return sorted(menu.values(), key=itemgetter('label'))


class Formula():
    """
    entity_id is accessed from FExpression.fetch_path_from_db() method
    """
    def __init__(self, db, user_locale, created_by, property_id, formula=None, entity_id=None):
        self.db                     = db
        self.formula                = formula
        self.entity_id              = entity_id
        self.value                  = []
        self.user_locale            = user_locale
        self.created_by             = created_by

        self.formula_property_id    = property_id

        # logging.debug('Formula.init')

    def evaluate(self):
        if not self.formula:
            return ''

        for m in re.findall(r"([^{]*){([^{}]*)}|(.*?)$",self.formula):
            if m[0]:
                self.value.append(m[0].encode('utf8'))
            if m[1]:
                self.value.append('%s'.encode('utf8') % ','.join(['%s' % x for x in FExpression(self, m[1]).value]))
            if m[2]:
                self.value.append(m[2].encode('utf8'))

        return self.value

    def save_property(self, new_property_id, old_property_id):

        self.db.execute('UPDATE property SET value_formula = %s WHERE id = %s;', self.formula, new_property_id)


class FExpression():
    def __init__(self, formula, xpr):
        self.db             = formula.db
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

            self.value = [', '.join(['%s' % x for x in _values])]
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
        # [{'value': 'A'}, {'value': 'SS'}, {'value': 'E'}]
        try:
            return sum([Decimal(v.value) for v in items])
        except Exception, e:
            return string([Decimal(v.value) for v in items])

    def FE_min(self, items):
        try:
            return min([Decimal(v.value) for v in items])
        except Exception, e:
            return string([Decimal(v.value) for v in items])

    def FE_max(self, items):
        try:
            return max([Decimal(v.value) for v in items])
        except Exception, e:
            return string([Decimal(v.value) for v in items])

    def FE_average(self, items):
        try:
            return Decimal(sum([Decimal(v.value) for v in items]) / len(items))
        except Exception, e:
            return string([Decimal(v.value) for v in items])

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

        if len(tokens) > 4:
            return []

        if tokens[0] == 'self':
            tokens[0] = self.formula.entity_id

        # Entity id:{self.id} is called {self.name}; and id:{6.id} description is {6.description}
        if len(tokens) == 2:
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
                AND e.is_deleted = 0
            """  % {'entity_id': tokens[0]}

            if tokens[1] != 'id':
                sql += """
                    AND p.is_deleted = 0
                    AND pd.dataproperty = '%(pdk)s'
                """ % {'pdk': tokens[1]}

            # logging.debug(sql)

            result = self.db.query(sql)

            # Entity {self.id} is called {self.name}, but {12.id} is called {12.name}

            return result

        # If second token is not one of relationship definition names,
        # then it has to be name of reference property
        # and third token has to be property name of referenced entity (entities);
        if tokens[1] not in ('child', 'viewer', 'expander', 'editor', 'owner', '-child', '-viewer', '-expander', '-editor', '-owner'):
            # also there should be exactly three tokens.
            if len(tokens) != 3:
                return []

            sql = 'SELECT ifnull(rep.value_decimal, ifnull(rep.value_string, ifnull(rep.value_text, ifnull(rep.value_integer, ifnull(rep.value_datetime, ifnull(rep.value_boolean, rep.value_file)))))) as value'
            if tokens[2] == 'id':
                sql = 'SELECT re.id as value'

            if tokens[1][:1] == '-':
                sql += """
                    FROM entity e
                    LEFT JOIN property p ON p.value_reference = e.id
                    LEFT JOIN property_definition pd ON pd.keyname = p.property_definition_keyname
                    LEFT JOIN entity re ON re.id = p.entity_id
                """
                tokens[1] = tokens[1][1:]
            else:
                sql += """
                    FROM entity e
                    LEFT JOIN property p ON p.entity_id = e.id
                    LEFT JOIN property_definition pd ON pd.keyname = p.property_definition_keyname
                    LEFT JOIN entity re ON re.id = p.value_reference
                """

            if tokens[2] != 'id':
                sql += """
                    LEFT JOIN property rep ON rep.entity_id = re.id
                    LEFT JOIN property_definition repd ON repd.keyname = rep.property_definition_keyname
                """

            sql += """
                WHERE e.id = %(entity_id)s
                AND e.is_deleted = 0
                AND p.is_deleted = 0
                AND pd.is_deleted = 0
                AND re.is_deleted = 0
                AND pd.dataproperty = '%(pdk)s'
            """  % {'entity_id': self.formula.entity_id, 'pdk': tokens[1]}

            if tokens[2] != 'id':
                sql += """
                    AND rep.is_deleted = 0
                    AND repd.is_deleted = 0
                    AND repd.dataproperty = '%(repdk)s'
                """  % {'repdk': tokens[2]}

            # logging.debug(sql)

            # There are {COUNT(self.child.folder.id)} folders called {self.child.folder.name}

            return self.db.query(sql)


        if len(tokens) != 4:
            return []

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
            AND re.is_deleted = 0
            AND e.is_deleted = 0
            AND r.is_deleted = 0
        """  % {'entity_id': self.formula.entity_id, 'rdk': tokens[1]}

        if tokens[2] != '*':
            sql += """
                AND re.entity_definition_keyname = '%(edk)s'
            """  % {'edk': tokens[2]}

        if tokens[3] != 'id':
            sql += """
                AND p.is_deleted = 0
                AND pd.dataproperty = '%(pdk)s'
            """ % {'pdk': tokens[3]}

        # logging.debug(sql)

        # There are {COUNT(self.child.folder.id)} folders called {self.child.folder.name}

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
        pass
        # logging.debug(m)


def sortableDateTime(s_date):
    if not s_date:
        return ''
    formatted_date = '%(year)d%(month)02d%(day)02d%(hour)02d%(minute)02d%(second)02d' % {'year': s_date.year, 'month': s_date.month, 'day': s_date.day, 'hour': s_date.hour, 'minute': s_date.minute, 'second': s_date.second}
    # logging.debug(formatted_date)
    return formatted_date


def sortableInteger(s_integer):
    return sortableDecimal(s_integer)


def sortableDecimal(s_decimal):
    if not s_decimal:
        return ''
    return '%016.4f' % s_decimal


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
