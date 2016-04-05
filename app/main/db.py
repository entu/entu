from tornado import locale

from datetime import datetime
from decimal import Decimal
from operator import itemgetter

import dateutil
import hashlib
import logging
import math
import os
import random
import re
import string
import time

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
        if not self.current_user.get('id'):
            return None
        return self.current_user.get('id')

    @property
    def __language(self):
        return self.get_user_locale().code

    def __get_system_translation(self, field, entity_definition_keyname='', property_definition_keyname=''):
        if not self.__translation:
            self.__translation = {}
            for t in self.db_query('SELECT field, value, IFNULL(entity_definition_keyname, \'\') AS entity_definition_keyname, IFNULL(property_definition_keyname, \'\') AS property_definition_keyname FROM translation WHERE language = %s OR language IS NULL ORDER BY language;', self.get_user_locale().code):
                self.__translation['%s|%s|%s' % (t.get('entity_definition_keyname'), t.get('property_definition_keyname'), t.get('field'))] = t.get('value')
        return self.__translation.get('%s|%s|%s' % (entity_definition_keyname, property_definition_keyname, field), None)

    def create_entity(self, entity_definition_keyname, parent_entity_id=None, ignore_user=False):
        """
        Creates new Entity and returns its ID.

        """

        if ignore_user == True:
            user_id = None
        else:
            if not self.__user_id:
                return
            user_id = self.__user_id

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
        entity_id = self.db_execute_lastrowid(sql, entity_definition_keyname, user_id)

        if not parent_entity_id:
            return entity_id

        # Propagate sharing
        parent = self.db_get('SELECT sharing FROM entity WHERE id = %s LIMIT 1;', parent_entity_id)
        self.db_execute('UPDATE entity SET sharing = %s WHERE id = %s LIMIT 1;', parent.get('sharing'), entity_id)

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
        self.db_execute(sql, entity_id, user_id, entity_definition_keyname, parent_entity_id, entity_id, user_id)

        # Insert or update "contains" information
        for row in self.db_query("SELECT entity_id FROM relationship r WHERE r.is_deleted = 0 AND r.relationship_definition_keyname = 'child' AND r.related_entity_id = %s" , entity_id):
            self.db_execute('INSERT INTO dag_entity SET entity_id = %s, related_entity_id = %s ON DUPLICATE KEY UPDATE distance=1;', row.get('entity_id'), entity_id)
            self.db_execute('INSERT INTO dag_entity SELECT de.entity_id, %s, de.distance+1 FROM dag_entity AS de WHERE de.related_entity_id = %s ON DUPLICATE KEY UPDATE distance = LEAST(dag_entity.distance, de.distance+1);', entity_id, row.get('entity_id'))

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
        self.db_execute(sql, entity_id, user_id, entity_id)

        # set creator to owner
        if user_id:
            self.set_rights(entity_id=entity_id, related_entity_id=user_id, right='owner')

        # Populate default values
        for default_value in self.db_query('SELECT keyname, defaultvalue FROM property_definition WHERE entity_definition_keyname = %s AND defaultvalue IS NOT null', entity_definition_keyname):
            self.set_property(entity_id=entity_id, property_definition_keyname=default_value.get('keyname'), value=default_value.get('defaultvalue'))

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
        self.db_execute(sql, entity_id, user_id, parent_entity_id)

        self.db_execute("""
            INSERT INTO property (property_definition_keyname, entity_id, value_display, value_datetime, created_by, created)
            SELECT keyname, %s, NOW(), NOW(), %s, NOW()
            FROM property_definition
            WHERE dataproperty = 'entu-created-at'
            AND entity_definition_keyname = %s;
        """, entity_id, user_id, entity_definition_keyname)

        if user_id:
            self.db_execute("""
                INSERT INTO property (property_definition_keyname, entity_id, value_reference, created_by, created)
                SELECT keyname, %s, %s, %s, NOW()
                FROM property_definition
                WHERE dataproperty = 'entu-created-by'
                AND entity_definition_keyname = %s;
            """, entity_id, user_id, user_id, entity_definition_keyname)

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
            new_entity_id = self.db_execute_lastrowid("""
                INSERT INTO entity (
                    entity_definition_keyname,
                    sharing,
                    created,
                    created_by
                ) SELECT
                    entity_definition_keyname,
                    sharing,
                    NOW(),
                    %s
                FROM entity
                WHERE id = %s;
            """ , self.__user_id, entity_id)

            self.db_execute("""
                INSERT INTO property (
                    property_definition_keyname,
                    entity_id,
                    ordinal,
                    language,
                    value_display,
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
                    property_definition_keyname,
                    %s,
                    ordinal,
                    language,
                    value_display,
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

            self.db_execute("""
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

            self.db_execute("""
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

            self.db_execute("""
                INSERT INTO property (property_definition_keyname, entity_id, value_display, value_datetime, created_by, created)
                SELECT keyname, %s, NOW(), NOW(), %s, NOW()
                FROM property_definition
                WHERE dataproperty = 'entu-created-at'
                AND entity_definition_keyname = (SELECT entity_definition_keyname FROM entity WHERE id = %s LIMIT 1);
            """, new_entity_id, self.__user_id, new_entity_id)

            self.db_execute("""
                INSERT INTO property (property_definition_keyname, entity_id, value_reference, created_by, created)
                SELECT keyname, %s, %s, %s, NOW()
                FROM property_definition
                WHERE dataproperty = 'entu-created-by'
                AND entity_definition_keyname = (SELECT entity_definition_keyname FROM entity WHERE id = %s LIMIT 1);
            """, new_entity_id, self.__user_id, self.__user_id, new_entity_id)

    def delete_entity(self, entity_id):
        if not self.db_get("""
                SELECT entity_id
                FROM relationship
                WHERE relationship_definition_keyname IN ('owner')
                AND entity_id = %s
                AND related_entity_id = %s
                AND is_deleted = 0;
            """,
            entity_id,
            self.__user_id
        ):
            return

        for child_id in self.get_relatives(ids_only=True, entity_id=entity_id, relationship_definition_keyname='child'):
            self.delete_entity(child_id)

        self.db_execute('UPDATE entity SET deleted = NOW(), is_deleted = 1, deleted_by = %s WHERE id = %s;', self.__user_id, entity_id)

        # remove "contains" information
        self.db_execute('DELETE FROM dag_entity WHERE entity_id = %s OR related_entity_id = %s;', entity_id, entity_id)

        return True

    def set_property(self, entity_id=None, relationship_id=None, property_definition_keyname=None, value=None, old_property_id=None, uploaded_file=None, ignore_user=False):
        """
        Saves property value. Creates new one if old_property_id = None. Returns new_property_id.

        """
        if not entity_id:
            return

        if ignore_user == True:
            user_id = None
        else:
            if not self.__user_id:
                return
            user_id = self.__user_id

        # property_definition_keyname is preferred because it could change for existing property
        if old_property_id:
            definition = self.db_get('SELECT pd.keyname, pd.datatype, pd.formula FROM property p, property_definition pd WHERE pd.keyname = p.property_definition_keyname AND p.id = %s LIMIT 1;', old_property_id)
        elif property_definition_keyname:
            definition = self.db_get('SELECT keyname, datatype, formula FROM property_definition WHERE keyname = %s LIMIT 1;', property_definition_keyname)
        else:
            return

        if not definition:
            return

        if old_property_id:
            self.db_execute('UPDATE property SET deleted = NOW(), is_deleted = 1, deleted_by = %s WHERE id = %s;', user_id, old_property_id)
            self.db_execute('UPDATE entity SET changed = NOW(), changed_by = %s WHERE id = %s;', user_id, entity_id)

        if self.db_get("""
            SELECT property.id
            FROM property, property_definition
            WHERE property_definition.keyname = property.property_definition_keyname
            AND property.entity_id = %s
            AND property_definition.dataproperty = 'entu-changed-at'
            LIMIT 1;
        """, entity_id):
            self.db_execute("""
                UPDATE property, property_definition
                SET property.value_display = NOW(), property.value_datetime = NOW(), property.created_by = %s, property.created = NOW()
                WHERE property_definition.keyname = property.property_definition_keyname
                AND property.entity_id = %s
                AND property_definition.dataproperty = 'entu-changed-at';
            """, user_id, entity_id)
        else:
            self.db_execute("""
                INSERT INTO property (property_definition_keyname, entity_id, value_display, value_datetime, created_by, created)
                SELECT keyname, %s, NOW(), NOW(), %s, NOW()
                FROM property_definition
                WHERE dataproperty = 'entu-changed-at'
                AND entity_definition_keyname = (SELECT entity_definition_keyname FROM entity WHERE id = %s LIMIT 1);
            """, entity_id, user_id, entity_id)

        if user_id:
            if self.db_get("""
                SELECT property.id
                FROM property, property_definition
                WHERE property_definition.keyname = property.property_definition_keyname
                AND property.entity_id = %s
                AND property_definition.dataproperty = 'entu-changed-by'
                LIMIT 1;
            """, entity_id):
                self.db_execute("""
                    UPDATE property, property_definition
                    SET property.value_display = NULL, property.value_reference = %s, property.created_by = %s, property.created = NOW()
                    WHERE property_definition.keyname = property.property_definition_keyname
                    AND property.entity_id = %s
                    AND property_definition.dataproperty = 'entu-changed-by';
                """, user_id, user_id, entity_id)
            else:
                self.db_execute("""
                    INSERT INTO property (property_definition_keyname, entity_id, value_reference, created_by, created)
                    SELECT keyname, %s, %s, %s, NOW()
                    FROM property_definition
                    WHERE dataproperty = 'entu-changed-by'
                    AND entity_definition_keyname = (SELECT entity_definition_keyname FROM entity WHERE id = %s LIMIT 1);
                """, entity_id, user_id, user_id, entity_id)

        # If no value, then property is deleted, return
        if not value:
            self.set_mongodb_entity(entity_id)
            return

        value_display = None

        if definition.get('formula') == 1:
            field = 'value_formula'
        elif definition.get('datatype') == 'text':
            field = 'value_text'
            value_display = '%s' % value
            value_display = value_display[:500]
        elif definition.get('datatype') == 'integer':
            field = 'value_integer'
            value_display = '%s' % value
        elif definition.get('datatype') == 'decimal':
            field = 'value_decimal'
            value = value.replace(',', '.')
            value = float(re.sub(r'[^\.0-9:]', '', value))
            value_display = round(value, 2)
        elif definition.get('datatype') == 'date':
            field = 'value_datetime'
            value_display = '%s' % value
        elif definition.get('datatype') == 'datetime':
            field = 'value_datetime'
            value_display = '%s' % value
        elif definition.get('datatype') == 'reference':
            field = 'value_reference'
            r = self.__get_properties(entity_id=value)
            if r:
                value_display = self.__get_properties(entity_id=value)[0]['displayname']
        elif definition.get('datatype') == 'file':
            uploaded_file = value
            field = 'value_file'
            value_display = uploaded_file['filename'][:500]

            if uploaded_file.get('url'):
                value = self.db_execute_lastrowid('INSERT INTO file SET url = %s, filename = %s, created_by = %s, created = NOW();', uploaded_file.get('url', ''), uploaded_file.get('filename', ''), user_id)
            elif uploaded_file.get('s3key'):
                value = self.db_execute_lastrowid('INSERT INTO file SET s3_key = %s, filename = %s, filesize = %s, created_by = %s, created = NOW();', uploaded_file.get('s3key', ''), uploaded_file.get('filename', ''), uploaded_file.get('filesize', ''), user_id)
            else:
                md5 = hashlib.md5(uploaded_file.get('body')).hexdigest()
                directory = os.path.join('/', 'entu', 'files', self.app_settings('database-name'), md5[0])
                filename = os.path.join(directory, md5)

                if not os.path.exists(directory):
                    os.makedirs(directory)
                f = open(filename, 'w')
                f.write(uploaded_file.get('body', ''))
                f.close()

                value = self.db_execute_lastrowid('INSERT INTO file SET md5 = %s, filename = %s, filesize = %s, created_by = %s, created = NOW();', md5, uploaded_file.get('filename', ''), len(uploaded_file.get('body', '')), user_id)

        elif definition.get('datatype') == 'boolean':
            field = 'value_boolean'
            value = 1 if value.lower() == 'true' else 0
            value_display = '%s' % bool(value)
        elif definition.get('datatype') == 'counter':
            field = 'value_counter'
            value_display = '%s' % value
        else:
            field = 'value_string'
            value = value[:500]
            value_display = '%s' % value

        new_property_id = self.db_execute_lastrowid("""
            INSERT INTO property SET
                entity_id = %%s,
                property_definition_keyname = %%s,
                %s = %%s,
                value_display = %%s,
                created = NOW(),
                created_by = %%s;
            """ % field,
            entity_id,
            definition.get('keyname'),
            value,
            value_display,
            user_id
        )

        if definition.get('datatype') == 'file' and uploaded_file.get('s3key'):
            self.db_execute('UPDATE file SET s3_key = CONCAT(s3_key, \'/\', %s) WHERE id = %s LIMIT 1;', new_property_id, value)

        self.db_execute('UPDATE entity SET changed = NOW(), changed_by = %s WHERE id = %s;', user_id, entity_id)

        self.set_mongodb_entity(entity_id)

        return new_property_id

    def set_mongodb_entity(self, entity_id):
        sql = """
            SELECT
                REPLACE(REPLACE(e.entity_definition_keyname, '_', '-'), '.', '-') AS entity_definition,
                e.id         AS entity_id,
                e.sharing    AS entity_sharing,
                e.created    AS entity_created,
                IF(CAST(e.created_by AS UNSIGNED) > 0, CAST(e.created_by AS UNSIGNED), NULL) AS entity_created_by,
                e.changed    AS entity_changed,
                IF(CAST(e.changed_by AS UNSIGNED) > 0, CAST(e.changed_by AS UNSIGNED), NULL) AS entity_changed_by,
                e.deleted    AS entity_deleted,
                IF(CAST(e.deleted_by AS UNSIGNED) > 0, CAST(e.deleted_by AS UNSIGNED), NULL) AS entity_deleted_by,
                e.is_deleted AS entity_is_deleted,
                e.old_id     AS entity_old_id
            FROM
                entity AS e
            WHERE e.id = %s
            LIMIT 1;
        """

        r = self.db_get(sql, entity_id)

        mysql_id = r.get('entity_id')

        e = {}
        e['_mid'] = mysql_id
        e['_definition'] = r.get('entity_definition')
        e['_sharing'] = r.get('entity_sharing')

        if r.get('entity_created'):
            e.setdefault('_created', {})['at'] = r.get('entity_created')
        if r.get('entity_created_by'):
            e.setdefault('_created', {})['by'] = r.get('entity_created_by')
        if e.get('_created'):
            e['_created']['type'] = 'action'
            e['_created'] = [e.get('_created')]

        if r.get('entity_changed'):
            e.setdefault('_changed', {})['at'] = r.get('entity_changed')
        if r.get('entity_changed_by'):
            e.setdefault('_changed', {})['by'] = r.get('entity_changed_by')
        if e.get('_changed'):
            e['_changed']['type'] = 'action'
            e['_changed'] = [e.get('_changed')]

        if r.get('entity_is_deleted') and r.get('entity_deleted'):
            e.setdefault('_deleted', {})['at'] = r.get('entity_deleted')
        if r.get('entity_is_deleted') and r.get('entity_deleted_by'):
            e.setdefault('_deleted', {})['by'] = r.get('entity_deleted_by')
        if e.get('_deleted'):
            e['_deleted']['type'] = 'action'
            e['_deleted'] = [e.get('_deleted')]

        viewers = self.__get_mongodb_right(mysql_id, ['viewer', 'expander', 'editor', 'owner'])
        if viewers:
            e['_viewer'] = [{'reference': x, 'type': 'reference'} for x in list(set(viewers))]

        expanders = self.__get_mongodb_right(mysql_id, ['expander', 'editor', 'owner'])
        if expanders:
            e['_expander'] = [{'reference': x, 'type': 'reference'} for x in list(set(expanders))]

        editors = self.__get_mongodb_right(mysql_id, ['editor', 'owner'])
        if editors:
            e['_editor'] = [{'reference': x, 'type': 'reference'} for x in list(set(editors))]

        owners = self.__get_mongodb_right(mysql_id, ['owner'])
        if owners:
            e['_owner'] = [{'reference': x, 'type': 'reference'} for x in list(set(owners))]

        parent = self.__get_mongodb_parent(entity_id=mysql_id, recursive=False)
        if parent:
            e['_parent'] = [{'reference': x, 'type': 'reference'} for x in list(set(parent))]

        ancestor = self.__get_mongodb_parent(entity_id=mysql_id, recursive=True)
        if ancestor:
            e['_ancestor'] = [{'reference': x, 'type': 'reference'} for x in list(set(ancestor))]

        sql = """
            SELECT
                p.id                    AS property_id,
                REPLACE(REPLACE(pd.dataproperty, '-', '_'), '.', '_')  AS property_dataproperty,
                pd.datatype             AS property_datatype,
                pd.formula              AS property_formula,
                pd.search               AS property_search,
                IF(pd.multilingual = 1, IF(p.language = 'english', 'en', 'et'), NULL) AS property_language,
                TRIM(p.value_formula)   AS value_formula,
                TRIM(p.value_string)    AS value_string,
                TRIM(p.value_text)      AS value_text,
                TRIM(p.value_display)   AS value_display,
                p.value_integer,
                p.value_decimal,
                p.value_boolean,
                p.value_datetime,
                p.value_reference,
                p.value_file,
                IF(pd.datatype = 'file', (SELECT s3_key FROM file WHERE id = p.value_file AND deleted IS NULL LIMIT 1), NULL) AS value_file_s3,
                IF(pd.datatype = 'file', (SELECT md5 FROM file WHERE id = p.value_file AND deleted IS NULL LIMIT 1), NULL) AS value_file_md5,
                IF(pd.datatype = 'file', (SELECT filename FROM file WHERE id = p.value_file AND deleted IS NULL LIMIT 1), NULL) AS value_file_name,
                IF(pd.datatype = 'file', (SELECT filesize FROM file WHERE id = p.value_file AND deleted IS NULL LIMIT 1), NULL) AS value_file_size,
                IF(pd.datatype = 'file', (SELECT url FROM file WHERE id = p.value_file AND deleted IS NULL LIMIT 1), NULL) AS value_file_url,
                p.value_counter,
                p.created,
                IF(CAST(p.created_by AS UNSIGNED) > 0, CAST(p.created_by AS UNSIGNED), NULL) AS created_by,
                p.is_deleted,
                p.deleted,
                IF(CAST(p.deleted_by AS UNSIGNED) > 0, CAST(p.deleted_by AS UNSIGNED), NULL) AS deleted_by
            FROM
                property AS p,
                property_definition AS pd
            WHERE pd.keyname = p.property_definition_keyname
            AND p.entity_id = %s
            AND p.is_deleted = 0
            AND pd.dataproperty NOT IN ('entu-changed-by', 'entu-changed-at', 'entu-created-by', 'entu-created-at')
            AND pd.dataproperty NOT LIKE 'auth_%%'
            AND pd.datatype NOT IN ('counter')
            AND pd.formula = 0;
        """

        properties = {}
        for r2 in self.db_query(sql, mysql_id):
            value = {}

            if r2.get('property_datatype') == 'string' and r2.get('value_string'):
                value['value'] = r2.get('value_string')
            elif r2.get('property_datatype') == 'text' and r2.get('value_text'):
                value['value'] = r2.get('value_text')
            elif r2.get('property_datatype') == 'integer' and r2.get('value_integer') != None:
                value['value'] = r2.get('value_integer')
            elif r2.get('property_datatype') == 'decimal' and r2.get('value_decimal') != None:
                value['value'] = float(r2.get('value_decimal'))
            elif r2.get('property_datatype') == 'boolean' and r2.get('value_boolean') != None:
                value['value'] = bool(r2.get('value_boolean'))
            elif r2.get('property_datatype') in ['date', 'datetime'] and r2.get('value_datetime') != None:
                value['value'] = r2.get('value_datetime')
            elif r2.get('property_datatype') == 'reference' and r2.get('value_reference'):
                value['reference'] = r2.get('value_reference')
            elif r2.get('property_datatype') == 'counter-value' and r2.get('value_string'):
                value['value'] = r2.get('value_string')
            elif r2.get('property_datatype') == 'file' and r2.get('value_file'):
                value['value'] = r2.get('value_file_name')
                if r2.get('value_file_url'):
                    value['url'] = r2.get('file')
                else:
                    value['size'] = r2.get('value_file_size')
                    if r2.get('value_file_md5', None):
                        value['md5'] = r2.get('value_file_md5')
                    if r2.get('value_file_s3', None):
                        value['s3'] = r2.get('value_file_s3')

            if not value:
                continue

            value['_mid'] = r2.get('property_id')
            value['type'] = r2.get('property_datatype')

            if r2.get('property_language'):
                value['language'] = r2.get('property_language')

            # if r2.get('created'):
            #     value.setdefault('created', {})['at'] = r2.get('created')
            # if r2.get('created_by'):
            #     value.setdefault('created', {})['by'] = r2.get('created_by')
            #
            # if r2.get('is_deleted') and r2.get('deleted'):
            #     value.setdefault('deleted', {})['at'] = r2.get('deleted')
            # if r2.get('is_deleted') and r2.get('deleted_by'):
            #     value.setdefault('deleted', {})['by'] = r2.get('deleted_by')

            e.setdefault(r2.get('property_dataproperty'), []).append(value)

            # if r2.get('value_display') and r2.get('property_search') == 1:
            #     if r2.get('property_language'):
            #         e.setdefault('_search', {}).setdefault(r2.get('property_language'), []).append(r2.get('value_display').lower())
            #     else:
            #         e.setdefault('_search', {}).setdefault('et', []).append(r2.get('value_display').lower())
            #         e.setdefault('_search', {}).setdefault('en', []).append(r2.get('value_display').lower())

        # for l in ['et', 'en']:
        #     if l in e.get('_search', {}):
        #         e['_search'][l] = list(set(e['_search'][l]))

        #Create or replace Mongo object
        try:
            mongo_entity_version = self.mongodb().entityVersion.find_one({'_mid': mysql_id}, {'_id': False, '_entity': True})
            if mongo_entity_version:
                e['_entity'] = mongo_entity_version.get('_entity')
            else:
                e['_entity'] = self.mongodb().entity.insert_one({}).inserted_id
            self.mongodb().entityVersion.insert_one(e)
        except Exception, err:
            self.captureException()
            logging.error('MongoDb error: %s - %s' % (err, e))

    def __get_mongodb_parent(self, entity_id, recursive=False):
        sql = """
            SELECT entity_id
            FROM relationship
            WHERE relationship_definition_keyname = 'child'
            AND is_deleted = 0
            AND entity_id IS NOT NULL
            AND related_entity_id = %s
        """ % entity_id

        entities = []
        for r in self.db_query(sql):
            entities.append(r.get('entity_id'))
            if recursive:
                entities = entities + self.__get_mongodb_parent(entity_id=r.get('entity_id'), recursive=True)

        return entities

    def __get_mongodb_right(self, entity_id, rights):
        sql = """
            SELECT related_entity_id
            FROM relationship
            WHERE relationship_definition_keyname IN (%s)
            AND is_deleted = 0
            AND related_entity_id IS NOT NULL
            AND entity_id = %s
        """ % (', '.join(['\'%s\'' % x for x in rights]), entity_id)

        entities = []
        for r in self.db_query(sql):
            entities.append(r.get('related_entity_id'))

        return entities

    def set_counter(self, entity_id):
        """
        Sets counter property.
        Counter mechanics is real hack. It will soon be obsoleted by formula field.
        """
        if not entity_id:
            return

        #Vastuskirja hack
        if self.db_get('SELECT entity_definition_keyname FROM entity WHERE id = %s', entity_id).get('entity_definition_keyname') == 'reply':
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


        property_id = self.db_execute_lastrowid("""
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
        """ % {'entity_id': entity_id, 'user_id': self.__user_id})

        self.db_execute("""
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
        """ % {'entity_id': entity_id, 'user_id': self.__user_id})

        self.db_execute('UPDATE property SET value_display = value_string WHERE id = %s', property_id)

        return self.db_get('SELECT value_string FROM property WHERE id = %s', property_id).get('value_string')

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
                    self.db_execute('UPDATE entity SET changed = NOW() WHERE entity.id = %s;', r if t == 'child' else e)
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
                        self.db_execute(sql)
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
                        old = self.db_execute_rowcount(sql)
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
                            self.db_execute(sql)
                    else:
                        sql = """
                            SELECT id
                            FROM relationship
                            WHERE relationship_definition_keyname = '%s'
                            AND entity_id = %s
                            AND related_entity_id = %s
                            AND is_deleted = 0;
                        """ % (t, e, r)
                        old = self.db_get(sql)
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
                            self.db_execute(sql)

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

            relationship = self.db_query(sql, right, entity_id)
            if not relationship:
                continue

            ids = [x.get('related_entity_id') for x in relationship if x.get('related_entity_id')]
            if ids:
                entities = self.__get_properties(entity_id=ids, full_definition=False, only_public=False)
                if entities:
                    rights[right] = entities

        return rights

    def set_rights(self, entity_id, related_entity_id, right=None, ignore_user=False):
        if not entity_id or not related_entity_id:
            return

        if ignore_user == True:
            user_id = None
        else:
            if not self.__user_id:
                return
            user_id = self.__user_id

        if type(entity_id) is not list:
            entity_id = [entity_id]

        if type(related_entity_id) is not list:
            related_entity_id = [related_entity_id]

        sql = """
            UPDATE relationship SET
                deleted = NOW(),
                is_deleted = 1,
                deleted_by = %%s
            WHERE is_deleted = 0
            AND relationship_definition_keyname IN ('viewer', 'expander', 'editor', 'owner')
            AND entity_id IN (%s)
            AND related_entity_id IN (%s);
        """ % (','.join(map(str, entity_id)), ','.join(map(str, related_entity_id)))
        self.db_execute(sql, user_id)

        if right in ['viewer', 'expander', 'editor', 'owner']:
            for e in entity_id:
                for re in related_entity_id:
                    self.db_execute('INSERT INTO relationship SET relationship_definition_keyname = %s, entity_id = %s, related_entity_id = %s, created = NOW(), created_by = %s;', right, int(e), int(re), user_id)

        self.db_execute('UPDATE entity SET changed = NOW() WHERE entity.id IN (%s);' % ','.join(map(str, entity_id)))

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

        self.db_execute(sql, sharing, self.__user_id)

    def set_sharing_key(self, entity_id, generate=False):
        if not entity_id:
            return

        if generate:
            sharing_key = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(64))
        else:
            sharing_key = None

        if type(entity_id) is not list:
            entity_id = [entity_id]

        sql = """
            UPDATE entity SET
                sharing_key = %%s,
                changed = NOW(),
                changed_by = %%s
            WHERE id IN (%s);
        """ % ','.join(map(str, entity_id))

        self.db_execute(sql, sharing_key, self.__user_id)

        return sharing_key

    def get_users(self, search=None):
        """
        To return list of entities that have
        'entu-user' or 'entu-api-key' property.
        """

        query_re = ''
        if search != None:
            join_parts = []
            for s in search.split(' ')[:5]:
                if not s:
                    continue
                join_parts.append('AND sp.value_display REGEXP(\'%(qs)s\')' % {'qs': s})
            query_re = ' '.join(join_parts)

        sql = """
            SELECT DISTINCT e.id AS id, sp.value_display, spd.*
            FROM entity AS e
            LEFT JOIN relationship AS r           ON r.entity_id  = e.id
            LEFT JOIN property AS p               ON p.entity_id = e.id
            RIGHT JOIN property_definition AS pd  ON p.property_definition_keyname = pd.keyname
                                                 AND pd.dataproperty IN ('entu-user','entu-api-key')
            LEFT JOIN property AS sp              ON sp.entity_id = e.id
            %(query_re)s
            LEFT JOIN property_definition AS spd ON spd.keyname = sp.property_definition_keyname
                                                 AND spd.is_deleted = 0
                                                 AND spd.search = 1
            WHERE e.is_deleted = 0
            AND r.is_deleted = 0
            AND p.is_deleted = 0
            AND sp.is_deleted = 0
            AND ( r.related_entity_id = %(user_id)i AND r.relationship_definition_keyname IN ('viewer', 'expander', 'editor', 'owner')
               OR e.sharing IN ('domain', 'public')
            ) ORDER BY e.sort, e.created DESC;
        """ % {'user_id': self.__user_id, 'query_re': query_re}
        # logging.debug(sql)
        ids = self.db_query(sql)
        # logging.debug(ids)

        entities = self.__get_properties(entity_id=[x.get('id') for x in ids])
        if not entities:
            return []

        return entities

    def get_entities(self, ids_only=False, entity_id=None, search=None, entity_definition_keyname=None, dataproperty=None, limit=None, full_definition=False, only_public=False, sharing_key=None):
        """
        If ids_only = True, then returns list of Entity IDs. Else returns list of Entities (with properties) as dictionary. entity_id, entity_definition and dataproperty can be single value or list of values.
        If limit = 1, then returns Entity (not list).
        If full_definition = True ,then returns also empty properties.

        """
        ids = self.__get_id_list(entity_id=entity_id, search=search, entity_definition_keyname=entity_definition_keyname, limit=limit, only_public=only_public, sharing_key=sharing_key)
        if ids_only == True:
            return ids

        entities = self.__get_properties(entity_id=ids, entity_definition_keyname=entity_definition_keyname, dataproperty=dataproperty, full_definition=full_definition, only_public=only_public, sharing_key=sharing_key)
        if not entities and full_definition == False and entity_definition_keyname == None:
            return

        if limit == 1 and len(entities) > 0:
            return entities[0]

        return entities

    def __get_id_list(self, entity_id=None, search=None, entity_definition_keyname=None, limit=None, only_public=False, sharing_key=None):
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

                where_parts.append('p%i.value_display LIKE \'%%%%%s%%%%\'' % (i, s))
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
        elif sharing_key:
            where_parts.append('e.sharing_key = \'%s\'' % sharing_key)
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

        items = self.db_query(sql)
        if not items:
            return []
        return [x.get('id') for x in items]

    # def formula_properties(self, entity_id):
    #     sql = """
    #         SELECT *
    #         FROM property p
    #         WHERE p.entity_id = %s
    #         AND p.value_formula is not null
    #         AND p.is_deleted = 0
    #         ORDER BY p.id
    #         ;""" % entity_id
    #     # logging.debug(sql)
    #     return self.db_query(sql)

    def __get_properties(self, entity_id=None, entity_definition_keyname=None, dataproperty=None, full_definition=False, only_public=False, sharing_key=None):
        """
        Get Entity properties. entity_id can be single ID or list of IDs.
        * full_definition - All metadata for entity and properties is fetched, if True
        """
        items = None
        if entity_id:
            if type(entity_id) is not list:
                entity_id = [entity_id]

            if self.__user_id and only_public == False:
                rights = '(SELECT relationship_definition_keyname FROM relationship WHERE entity_id = entity.id AND is_deleted = 0 AND related_entity_id = %s AND relationship_definition_keyname IN (\'viewer\', \'expander\', \'editor\', \'owner\') LIMIT 1)' % self.__user_id
                public = ''
            elif sharing_key:
                rights = 'FALSE'
                public = 'AND entity.sharing_key = \'%s\'' % sharing_key
            else:
                rights = 'FALSE'
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
                    entity.sharing_key                              AS entity_sharing_key,
                    %(rights)s                                      AS entity_right,
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
                    property.created                                AS value_created,
                    property.created_by                             AS value_created_by,
                    property.value_display                          AS value_display,
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
                AND entity.is_deleted = 0
                AND property.is_deleted = 0
                %(public)s
                %(datapropertysql)s
                ORDER BY
                    entity_definition.keyname,
                    entity.created DESC;
            """ % {'language': self.get_user_locale().code, 'public': public, 'idlist': ','.join(map(str, entity_id)), 'datapropertysql': datapropertysql, 'rights': rights}
            # logging.debug(sql)

            items = {}
            for row in self.db_query(sql):
                if row.get('entity_sharing') == 'private' and not row.get('entity_right') and not sharing_key:
                    continue
                if row.get('entity_sharing') in ['domain', 'public'] and row.get('entity_right') not in ['viewer', 'expander', 'editor', 'owner'] and row.get('property_public') != 1 and not sharing_key:
                    continue

                #Entity
                items.setdefault('item_%s' % row.get('entity_id'), {})['definition_keyname'] = row.get('entity_definition_keyname')
                items.setdefault('item_%s' % row.get('entity_id'), {})['id'] = row.get('entity_id')
                items.setdefault('item_%s' % row.get('entity_id'), {})['label'] = self.__get_system_translation(field='label', entity_definition_keyname=row.get('entity_definition_keyname'))
                items.setdefault('item_%s' % row.get('entity_id'), {})['label_plural'] = self.__get_system_translation(field='label_plural', entity_definition_keyname=row.get('entity_definition_keyname'))
                items.setdefault('item_%s' % row.get('entity_id'), {})['description'] = self.__get_system_translation(field='description', entity_definition_keyname=row.get('entity_definition_keyname'))
                items.setdefault('item_%s' % row.get('entity_id'), {})['sort'] = self.__get_system_translation(field='sort', entity_definition_keyname=row.get('entity_definition_keyname'))
                items.setdefault('item_%s' % row.get('entity_id'), {})['sort_value'] = row.get('entity_sort_value')
                items.setdefault('item_%s' % row.get('entity_id'), {})['created'] = row.get('entity_created')
                items.setdefault('item_%s' % row.get('entity_id'), {})['changed'] = row.get('entity_changed')
                items.setdefault('item_%s' % row.get('entity_id'), {})['displayname'] = self.__get_system_translation(field='displayname', entity_definition_keyname=row.get('entity_definition_keyname'))
                items.setdefault('item_%s' % row.get('entity_id'), {})['displayinfo'] = self.__get_system_translation(field='displayinfo', entity_definition_keyname=row.get('entity_definition_keyname'))
                items.setdefault('item_%s' % row.get('entity_id'), {})['displaytable'] = self.__get_system_translation(field='displaytable', entity_definition_keyname=row.get('entity_definition_keyname'))
                items.setdefault('item_%s' % row.get('entity_id'), {})['sharing'] = row.get('entity_sharing')
                items.setdefault('item_%s' % row.get('entity_id'), {})['sharing_key'] = row.get('entity_sharing_key')
                items.setdefault('item_%s' % row.get('entity_id'), {})['right'] = row.get('entity_right')
                items.setdefault('item_%s' % row.get('entity_id'), {})['ordinal'] = row.get('entity_created') if row.get('entity_created') else datetime.datetime.now()

                #Property
                items.setdefault('item_%s' % row.get('entity_id'), {}).setdefault('properties', {}).setdefault('%s' % row.get('property_dataproperty'), {})['keyname'] = row.get('property_keyname')
                items.setdefault('item_%s' % row.get('entity_id'), {}).setdefault('properties', {}).setdefault('%s' % row.get('property_dataproperty'), {})['fieldset'] = self.__get_system_translation(field='fieldset', property_definition_keyname=row.get('property_keyname'))
                items.setdefault('item_%s' % row.get('entity_id'), {}).setdefault('properties', {}).setdefault('%s' % row.get('property_dataproperty'), {})['label'] = self.__get_system_translation(field='label', property_definition_keyname=row.get('property_keyname'))
                items.setdefault('item_%s' % row.get('entity_id'), {}).setdefault('properties', {}).setdefault('%s' % row.get('property_dataproperty'), {})['label_plural'] = self.__get_system_translation(field='label_plural', property_definition_keyname=row.get('property_keyname'))
                items.setdefault('item_%s' % row.get('entity_id'), {}).setdefault('properties', {}).setdefault('%s' % row.get('property_dataproperty'), {})['description'] = self.__get_system_translation(field='description', property_definition_keyname=row.get('property_keyname'))
                items.setdefault('item_%s' % row.get('entity_id'), {}).setdefault('properties', {}).setdefault('%s' % row.get('property_dataproperty'), {})['datatype'] = row.get('property_datatype')
                items.setdefault('item_%s' % row.get('entity_id'), {}).setdefault('properties', {}).setdefault('%s' % row.get('property_dataproperty'), {})['dataproperty'] = row.get('property_dataproperty')
                items.setdefault('item_%s' % row.get('entity_id'), {}).setdefault('properties', {}).setdefault('%s' % row.get('property_dataproperty'), {})['mandatory'] = bool(row.get('property_mandatory'))
                items.setdefault('item_%s' % row.get('entity_id'), {}).setdefault('properties', {}).setdefault('%s' % row.get('property_dataproperty'), {})['multilingual'] = bool(row.get('property_multilingual'))
                items.setdefault('item_%s' % row.get('entity_id'), {}).setdefault('properties', {}).setdefault('%s' % row.get('property_dataproperty'), {})['multiplicity'] = row.get('property_multiplicity')
                items.setdefault('item_%s' % row.get('entity_id'), {}).setdefault('properties', {}).setdefault('%s' % row.get('property_dataproperty'), {})['ordinal'] = row.get('property_ordinal')
                items.setdefault('item_%s' % row.get('entity_id'), {}).setdefault('properties', {}).setdefault('%s' % row.get('property_dataproperty'), {})['formula'] = bool(row.get('property_formula'))
                items.setdefault('item_%s' % row.get('entity_id'), {}).setdefault('properties', {}).setdefault('%s' % row.get('property_dataproperty'), {})['executable'] = bool(row.get('property_executable'))
                items.setdefault('item_%s' % row.get('entity_id'), {}).setdefault('properties', {}).setdefault('%s' % row.get('property_dataproperty'), {})['public'] = bool(row.get('property_public'))
                items.setdefault('item_%s' % row.get('entity_id'), {}).setdefault('properties', {}).setdefault('%s' % row.get('property_dataproperty'), {})['readonly'] = bool(row.get('property_readonly'))
                items.setdefault('item_%s' % row.get('entity_id'), {}).setdefault('properties', {}).setdefault('%s' % row.get('property_dataproperty'), {})['visible'] = bool(row.get('property_visible'))

                #Value
                value = row.get('value_display') if row.get('value_display') else ''

                if row.get('property_formula') == 1:
                    db_value = row.get('value_formula')
                elif row.get('property_datatype') == 'string':
                    db_value = row.get('value_string')
                elif row.get('property_datatype') == 'text':
                    db_value = row.get('value_text')
                    value = row.get('value_text') if row.get('value_text') else ''
                elif row.get('property_datatype') == 'integer':
                    db_value = row.get('value_integer')
                elif row.get('property_datatype') == 'decimal':
                    db_value = row.get('value_decimal')
                elif row.get('property_datatype') == 'date':
                    db_value = row.get('value_datetime')
                elif row.get('property_datatype') == 'datetime':
                    db_value = row.get('value_datetime')
                elif row.get('property_datatype') == 'reference':
                    db_value = row.get('value_reference')
                elif row.get('property_datatype') == 'file':
                    db_value = row.get('value_file')
                elif row.get('property_datatype') == 'boolean':
                    db_value = row.get('value_boolean')
                elif row.get('property_datatype') == 'counter':
                    db_value = row.get('value_counter')
                elif row.get('property_datatype') == 'counter-value':
                    db_value = row.get('value_string')
                else:
                    db_value = ''
                    value = 'X'

                items.setdefault('item_%s' % row.get('entity_id'), {}).setdefault('properties', {}).setdefault('%s' % row.get('property_dataproperty'), {}).setdefault('values', {}).setdefault('value_%s' % row.get('value_id'), {})['id'] = row.get('value_id')
                items.setdefault('item_%s' % row.get('entity_id'), {}).setdefault('properties', {}).setdefault('%s' % row.get('property_dataproperty'), {}).setdefault('values', {}).setdefault('value_%s' % row.get('value_id'), {})['ordinal'] = row.get('value_ordinal')
                items.setdefault('item_%s' % row.get('entity_id'), {}).setdefault('properties', {}).setdefault('%s' % row.get('property_dataproperty'), {}).setdefault('values', {}).setdefault('value_%s' % row.get('value_id'), {})['value'] = value
                items.setdefault('item_%s' % row.get('entity_id'), {}).setdefault('properties', {}).setdefault('%s' % row.get('property_dataproperty'), {}).setdefault('values', {}).setdefault('value_%s' % row.get('value_id'), {})['db_value'] = db_value
                items.setdefault('item_%s' % row.get('entity_id'), {}).setdefault('properties', {}).setdefault('%s' % row.get('property_dataproperty'), {}).setdefault('values', {}).setdefault('value_%s' % row.get('value_id'), {})['created'] = row.get('value_created')
                items.setdefault('item_%s' % row.get('entity_id'), {}).setdefault('properties', {}).setdefault('%s' % row.get('property_dataproperty'), {}).setdefault('values', {}).setdefault('value_%s' % row.get('value_id'), {})['created_by'] = row.get('value_created_by')

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
                    reference_definition = self.db_get('SELECT classifying_entity_definition_keyname FROM property_definition WHERE keyname = %s LIMIT 1;', p_value['keyname'])
                    if reference_definition:
                        if reference_definition.get('classifying_entity_definition_keyname'):
                            items[key]['properties'][p_key]['reference_definition'] = reference_definition.get('classifying_entity_definition_keyname')
                if p_value['datatype'] == 'file':
                    for f_key, f_value in enumerate(p_value.get('values', {})):
                        if not f_value.get('db_value'):
                            continue
                        file_result = self.db_get('SELECT md5, filesize, created FROM file WHERE id = %s;', f_value.get('db_value'))
                        if not file_result:
                            continue
                        items[key]['properties'][p_key]['values'][f_key]['md5'] = file_result.get('md5')
                        items[key]['properties'][p_key]['values'][f_key]['filesize'] = file_result.get('filesize')
                        items[key]['properties'][p_key]['values'][f_key]['created'] = file_result.get('created')

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
                result[displayfield] = result[displayfield].replace('@%s@' % data_property, ', '.join(['%s' % x['value'] for x in dataproperty_dict.get('values', {}).values()])).replace('\n', ' ')

        result['displaytable_labels'] = self.__get_system_translation(field='displaytableheader', entity_definition_keyname=entity_dict.get('definition_keyname'))
        if not result['displaytable_labels']:
            result['displaytable_labels'] = entity_dict.get('displaytable', '') if entity_dict.get('displaytable', '') else None
            for data_property in findTags(entity_dict.get('displaytable', ''), '@', '@'):
                result['displaytable_labels'] = result['displaytable_labels'].replace('@%s@' % data_property, entity_dict.get('properties', {}).get(data_property, {}).get('label', ''))

        result['displaytable'] = result['displaytable'].split('|') if result['displaytable'] else None
        result['displaytable_labels'] = result['displaytable_labels'].split('|') if result['displaytable_labels'] else None

        if entity_dict.get('id', None) and entity_dict.get('sort_value', None) != result['sort']:
            self.db_execute('UPDATE entity SET sort = LEFT(%s, 100) WHERE id = %s', result['sort'], entity_dict.get('id'))

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
        f = self.db_get(sql, entity_id)
        if f:
            return '/api2/entity-%s/picture' % entity_id
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
                property_definition.formula AS property_formula,
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
        for r in self.db_query(sql):
            defs.append({
                'entity_definition_keyname': r.get('entity_definition_keyname'),
                'entity_label': self.__get_system_translation(field='label', entity_definition_keyname=r.get('entity_definition_keyname')),
                'entity_label_plural': self.__get_system_translation(field='label_plural', entity_definition_keyname=r.get('entity_definition_keyname')),
                'entity_description': self.__get_system_translation(field='description', entity_definition_keyname=r.get('entity_definition_keyname')),
                'entity_displayname': self.__get_system_translation(field='displayname', entity_definition_keyname=r.get('entity_definition_keyname')),
                'entity_displayinfo': self.__get_system_translation(field='displayinfo', entity_definition_keyname=r.get('entity_definition_keyname')),
                'entity_displaytable': self.__get_system_translation(field='displaytable', entity_definition_keyname=r.get('entity_definition_keyname')),
                'property_keyname': r.get('property_keyname'),
                'property_fieldset': self.__get_system_translation(field='fieldset', property_definition_keyname=r.get('property_keyname')),
                'property_label': self.__get_system_translation(field='label', property_definition_keyname=r.get('property_keyname')),
                'property_label_plural': self.__get_system_translation(field='label_plural', property_definition_keyname=r.get('property_keyname')),
                'property_description': self.__get_system_translation(field='description', property_definition_keyname=r.get('property_keyname')),
                'property_datatype': r.get('property_datatype'),
                'property_dataproperty': r.get('property_dataproperty'),
                'property_mandatory': bool(r.get('property_mandatory')),
                'property_multilingual': bool(r.get('property_multilingual')),
                'property_multiplicity': r.get('property_multiplicity'),
                'property_ordinal': r.get('property_ordinal'),
                'property_public': bool(r.get('property_public')),
                'property_readonly': bool(r.get('property_readonly')),
                'property_visible': bool(r.get('property_visible')),
                'property_classifier_id': r.get('property_classifier_id'),
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
        for d in self.db_query(sql):
            defs.append({
                'keyname': d.get('keyname'),
                'label': self.__get_system_translation(field='label', entity_definition_keyname=d.get('keyname')),
                'label_plural': self.__get_system_translation(field='label_plural', entity_definition_keyname=d.get('keyname')),
                'description': self.__get_system_translation(field='description', entity_definition_keyname=d.get('keyname')),
                'menugroup': self.__get_system_translation(field='menu', entity_definition_keyname=d.get('keyname')),
                'open_after_add': d.get('open_after_add'),
                'ordinal': d.get('ordinal'),
                'actions_add': d.get('actions_add')
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
            for item in self.db_query(sql):
                items.append(item.get('id'))
        elif relationship_ids_only == True:
            items = []
            for item in self.db_query(sql):
                items.append(item.get('relationship_id'))
        else:
            items = {}
            for item in self.db_query(sql):
                ent = self.__get_properties(entity_id=item.get('id'), full_definition=full_definition, entity_definition_keyname=entity_definition_keyname, only_public=only_public)
                if not ent:
                    continue
                ent = ent[0]
                items.setdefault('%s' % ent.get('label_plural', ''), []).append(ent)
        return items

    def get_file(self, file_id, sharing_key=None):
        """
        Returns file object. File properties are id, file, filename.

        """

        if type(file_id) is not list:
            file_id = [file_id]

        if self.__user_id:
            user_where = """
                AND p.entity_id IN (
                    SELECT entity_id
                    FROM relationship
                    WHERE relationship_definition_keyname IN ('viewer', 'expander', 'editor', 'owner')
                    AND is_deleted = 0
                    AND related_entity_id = %s
                    UNION SELECT id
                    FROM entity
                    WHERE sharing IN ('domain', 'public')
                    AND is_deleted = 0
                )
            """ % self.__user_id
        elif sharing_key:
            user_where = 'AND p.entity_id IN (SELECT id FROM entity WHERE sharing_key = \'%s\')' % sharing_key
        else:
            user_where = 'AND pd.public = 1'

        sql = """
            SELECT DISTINCT
                f.id,
                f.md5,
                f.filename,
                f.s3_key,
                f.url,
                f.created
            FROM
                file AS f,
                property AS p,
                property_definition AS pd
            WHERE p.value_file = f.id
            AND pd.keyname = p.property_definition_keyname
            AND f.id IN (%(file_id)s)
            %(user_where)s
            AND p.is_deleted = 0
            """ % {'file_id': ','.join(map(str, file_id)), 'user_where': user_where}
        # logging.debug(sql)

        result = []
        for f in self.db_query(sql):
            if f.get('md5'):
                filename = os.path.join('/', 'entu', 'files', self.app_settings('database-name'), f.get('md5')[0], f.get('md5'))
                if os.path.isfile(filename):
                    with open(filename, 'r') as myfile:
                        filecontent = myfile.read()
                else:
                    filecontent = None
            else:
                filecontent = None

            result.append({
                'id': f.get('id'),
                'created': f.get('created'),
                'file': filecontent,
                'filename': f.get('filename'),
                's3key': f.get('s3_key'),
                'url': f.get('url')
            })

        return result

    def get_allowed_childs(self, entity_id):
        """
        Returns allowed child definitions.

        """

        if not self.db_get('SELECT id FROM relationship WHERE relationship_definition_keyname iN (\'expander\', \'editor\', \'owner\') AND entity_id = %s AND related_entity_id = %s AND is_deleted = 0 LIMIT 1;', entity_id, self.__user_id):
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
        result = self.db_query(sql)

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
            result = self.db_query(sql)

        defs = []
        for d in result:
            defs.append({
                'keyname': d.get('keyname'),
                'label': self.__get_system_translation(field='label', entity_definition_keyname=d.get('keyname')),
                'label_plural': self.__get_system_translation(field='label_plural', entity_definition_keyname=d.get('keyname')),
                'description': self.__get_system_translation(field='description', entity_definition_keyname=d.get('keyname')),
                'menugroup': self.__get_system_translation(field='menu', entity_definition_keyname=d.get('keyname')),
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
        result = self.db_query(sql)

        defs = []
        for d in self.db_query(sql):
            defs.append({
                'keyname': d.get('keyname'),
                'label': self.__get_system_translation(field='label', entity_definition_keyname=d.get('keyname')),
                'label_plural': self.__get_system_translation(field='label_plural', entity_definition_keyname=d.get('keyname')),
                'description': self.__get_system_translation(field='description', entity_definition_keyname=d.get('keyname')),
                'menugroup': self.__get_system_translation(field='menu', entity_definition_keyname=d.get('keyname')),
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
        for d in self.db_query(sql):
            related_entity = self.get_entities(entity_id=d.get('related_entity_id'), limit=1)
            defs.append({
                'keyname': d.get('keyname'),
                'label': self.__get_system_translation(field='label', entity_definition_keyname=d.get('keyname')),
                'label_plural': self.__get_system_translation(field='label_plural', entity_definition_keyname=d.get('keyname')),
                'description': self.__get_system_translation(field='description', entity_definition_keyname=d.get('keyname')),
                'menugroup': self.__get_system_translation(field='menu', entity_definition_keyname=d.get('keyname')),
                'related_entity_id': d.get('related_entity_id'),
                'related_entity_label': related_entity.get('displayname') if related_entity else '',
            })

        return defs

    def get_public_paths(self):
        """
        Returns public paths with labels

        """

        paths = {}
        for i in self.db_query('SELECT DISTINCT keyname, public_path FROM entity_definition WHERE public_path IS NOT NULL ORDER BY public_path;'):
            paths[i.get('public_path')] = self.__get_system_translation(field='public', entity_definition_keyname=i.get('keyname'))
        return paths

    def get_public_path(self, entity_id):
        """
        Returns public path for entity
        Returns False, if public path does not exist

        """

        path = self.db_query("""
            SELECT ed.public_path
            FROM entity e
            LEFT JOIN entity_definition ed ON ed.keyname = e.entity_definition_keyname
            WHERE e.id = %s
            AND e.is_deleted = 0
            AND ed.is_deleted = 0
            AND e.sharing = 'public'
            AND ed.public_path IS NOT NULL
        """ % entity_id)
        return path

    def get_menu(self):
        """
        Returns user menu.

        """

        if self.__user_id:
            user_select = """
                SELECT
                    t.entity_definition_keyname,
                    t.field,
                    t.value,
                    (
                        SELECT entity.id
                        FROM entity
                        WHERE entity.entity_definition_keyname = t.entity_definition_keyname
                        AND entity.is_deleted = 0
                        AND entity.sharing IN ('domain', 'public')
                        LIMIT 1
                    ) AS x
                FROM
                    translation AS t
                WHERE t.field IN ('menu', 'label', 'label_plural')
                AND IFNULL(t.language, '%(language)s') = '%(language)s'
                HAVING x IS NOT NULL
                UNION SELECT
                    t.entity_definition_keyname,
                    t.field,
                    t.value,
                    (
                        SELECT entity.id
                        FROM entity, relationship
                        WHERE relationship.entity_id = entity.id
                        AND entity.entity_definition_keyname = t.entity_definition_keyname
                        AND entity.is_deleted = 0
                        AND relationship.is_deleted = 0
                        AND relationship.relationship_definition_keyname IN ('viewer', 'expander', 'editor', 'owner')
                        AND relationship.related_entity_id = %(user_id)s
                        LIMIT 1
                    ) AS x
                FROM
                    translation AS t
                WHERE t.field IN ('menu', 'label', 'label_plural')
                AND IFNULL(t.language, '%(language)s') = '%(language)s'
                HAVING x IS NOT NULL
            """ % {'user_id': self.__user_id, 'language': self.__language}
        else:
            user_select = """
                SELECT
                    t.entity_definition_keyname,
                    t.field,
                    t.value,
                    (
                        SELECT entity.id
                        FROM entity
                        WHERE entity.entity_definition_keyname = t.entity_definition_keyname
                        AND entity.is_deleted = 0
                        AND entity.sharing = 'public'
                        LIMIT 1
                    ) AS x
                FROM
                    translation AS t
                WHERE t.field IN ('menu', 'label', 'label_plural')
                AND IFNULL(t.language, '%(language)s') = '%(language)s'
                HAVING x IS NOT NULL
            """ % {'language': self.__language}


        sql = """
            SELECT
                entity_definition_keyname AS definition,
                MAX(IF(field='menu', value, NULL)) AS menu,
                MAX(IF(field='label', value, NULL)) AS label,
                MAX(IF(field='label_plural', value, NULL)) AS label_plural
            FROM (
                %s
            ) AS x
            GROUP BY definition
            HAVING menu IS NOT NULL
            ORDER BY
                menu,
                label_plural;
        """ % user_select
        # logging.debug(sql)

        menu = {}
        for m in self.db_query(sql):
            menu.setdefault(m.get('menu'), {})['label'] = m.get('menu')
            menu.setdefault(m.get('menu'), {}).setdefault('items', []).append({'keyname': m.get('definition'), 'title': m.get('label_plural')})

        return sorted(menu.values(), key=itemgetter('label'))


def findTags(s, beginning, end):
    """
    Finds and returns list of tags from string.

    """
    if not s:
        return []
    return re.compile('%s(.*?)%s' % (beginning, end), re.DOTALL).findall(s)
