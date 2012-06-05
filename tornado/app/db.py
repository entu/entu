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

        if self.user_id:
            if type(self.user_id) is not list:
                self.user_id = [self.user_id]

    def create(self, entity_definition_id, parent_entity_id):
        """
        Creates new Entity and returns its ID.

        """
        if not entity_definition_id or not parent_entity_id:
            return

        # Create entity
        sql = """
            INSERT INTO entity SET
                entity_definition_id = %s,
                created_by = %s,
                created = NOW();
        """
        # logging.info(sql)
        entity_id = self.db.execute_lastrowid(sql, entity_definition_id, ','.join(map(str, self.user_id)))

        # Insert child relationship
        sql = """
            INSERT INTO relationship SET
                type = 'child',
                entity_id = %s,
                related_entity_id = %s,
                created_by = %s,
                created = NOW();
        """
        # logging.info(sql)
        self.db.execute(sql, parent_entity_id, entity_id, ','.join(map(str, self.user_id)))

        # Copy user rights
        sql = """
            INSERT INTO relationship (
                type,
                entity_id,
                related_entity_id,
                created_by,
                created
            ) SELECT /* SQL_NO_CACHE */
                type,
                %s,
                related_entity_id,
                %s,
                NOW()
            FROM relationship
            WHERE type IN ('viewer', 'editor', 'owner')
            AND entity_id = %s;
        """
        # logging.info(sql)
        self.db.execute(sql, entity_id, ','.join(map(str, self.user_id)), parent_entity_id)

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
                value_reference,
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
                property.value_reference,
                property.value_file,
                property.value_counter,
                %s,
                NOW()
            FROM
                relationship,
                property_definition,
                property
            WHERE property_definition.id = relationship.property_definition_id
            AND property.property_definition_id = property_definition.id
            #AND property_definition.entity_definition_id = %s
            AND property.entity_id = %s
            AND type = 'propagated_property';
        """
        # logging.info(sql)
        self.db.execute(sql, entity_id, ','.join(map(str, self.user_id)), entity_definition_id, parent_entity_id)

        return entity_id

    def set_property(self, entity_id, property_definition_id, value, property_id=None, uploaded_file=None):
        """
        Saves property value. Creates new one if property_id = None.  Returns property ID.

        """
        if not entity_id or not property_definition_id:
            return

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
                value = self.db.execute_lastrowid('INSERT INTO file SET filename = %s, file = %s, created_by = %s, created = NOW();', uploaded_file['filename'], uploaded_file['body'], ','.join(map(str, self.user_id)))
            field = 'value_file'
        elif definition.datatype == 'boolean':
            field = 'value_boolean'
            value = 1 if value.lower() == 'true' else 0
        elif definition.datatype == 'counter':
            field = 'value_counter'
        else:
            field = 'value_string'
            value = value[:500]

        if property_id:
            self.db.execute('UPDATE property SET %s = %%s, changed = NOW(), changed_by = %%s WHERE id = %%s;' % field,
                value,
                ','.join(map(str, self.user_id)),
                property_id,
            )
        else:
            property_id = self.db.execute_lastrowid('INSERT INTO property SET entity_id = %%s, property_definition_id = %%s, %s = %%s, created = NOW(), created_by = %%s;' % field,
                entity_id,
                property_definition_id,
                value,
                ','.join(map(str, self.user_id))
            )

        return property_id

    def set_counter(self, entity_id):
        #Counters
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
                    AND entity.id = (SELECT entity_id FROM relationship WHERE related_entity_id = %(entity_id)s AND type='child' LIMIT 1)
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
                    AND entity.id = (SELECT entity_id FROM relationship WHERE related_entity_id = %(entity_id)s AND type='child' LIMIT 1)
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
            AND property.entity_id = (SELECT entity_id FROM relationship WHERE related_entity_id = %(entity_id)s AND type='child' LIMIT 1)
            AND property_definition.datatype= 'counter'
            AND property_definition2.datatype = 'counter_value'
            AND relationship.type = 'target_property'
            AND property_definition2.entity_definition_id = (SELECT entity_definition_id FROM entity WHERE id = %(entity_id)s LIMIT 1);
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
                AND property.entity_id = (SELECT entity_id FROM relationship WHERE related_entity_id = %(entity_id)s AND type='child' LIMIT 1)
                AND property_definition.datatype= 'counter'
                AND property_definition2.datatype = 'counter_value'
                AND relationship.type = 'target_property'
                AND property_definition2.entity_definition_id = (SELECT entity_definition_id FROM entity WHERE id = %(entity_id)s LIMIT 1)
                ) X
            SET counter.value = counter.value + counter.increment
            WHERE counter.id = X.id;
        """ % {'entity_id': entity_id, 'user_id': ','.join(map(str, self.user_id))}
        logging.info(sql)
        property_id = self.db.execute_lastrowid(sql)
        return self.db.get('SELECT value_string FROM property WHERE id=%s', property_id).value_string


    def get(self, ids_only=False, entity_id=None, search=None, entity_definition_id=None, limit=None, full_definition=False, public=False):
        """
        If ids_only = True, then returns list of Entity IDs. Else returns list of Entities (with properties) as dictionary. entity_id and entity_definition can be single ID or list of IDs. If limit = 1 returns Entity (not list). If full_definition = True returns also empty properties.

        """
        if public == True:
            self.user_id = None

        ids = self.__get_id_list(entity_id=entity_id, search=search, entity_definition_id=entity_definition_id, limit=limit)
        if ids_only == True:
            return ids

        entities = self.__get_properties(entity_id=ids)
        if not entities and full_definition == False and entity_definition_id == None:
            return

        if not entities:
            if type(entity_definition_id) is not list:
                entity_definition_id = [entity_definition_id]

            entities = []
            for e in entity_definition_id:
                entities.append({
                    'definition_id': entity_definition_id,
                })


        for entity in entities:
            if full_definition:
                for d in self.get_definition(entity_definition_id=entity['definition_id']):
                    if not entity.get('id', None):
                        entity['displayname'] = self.user_locale.translate('new_entity_label') % d.entity_label
                    entity.setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['id'] = d.property_id
                    entity.setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['label'] = d.property_label
                    entity.setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['label_plural'] = d.property_label_plural
                    entity.setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['description'] = d.property_description
                    entity.setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['datatype'] = d.property_datatype
                    entity.setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['dataproperty'] = d.property_dataproperty
                    entity.setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['multilingual'] = d.property_multilingual
                    entity.setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['multiplicity'] = d.property_multiplicity
                    entity.setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['ordinal'] = d.property_ordinal
                    if not d.property_multiplicity or d.property_multiplicity > len(entity.get('properties', {}).get('%s' % d.property_dataproperty, {}).get('values', {}).values()):
                        entity.setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {}).setdefault('values', {})['value_new'] = {'id': '', 'ordinal': 'X', 'value': '', 'db_value': ''}
                    if not d.property_multiplicity or d.property_multiplicity > len(entity.get('properties', {}).get('%s' % d.property_dataproperty, {}).get('values', {}).values()):
                        entity.setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['can_add_new'] = True
                    else:
                        entity.setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {})['can_add_new'] = False

                    if d.property_classifier_id:
                        for c in self.get(entity_definition_id=d.property_classifier_id, public=True):
                            if c.get('id', None):
                                entity.setdefault('properties', {}).setdefault('%s' % d.property_dataproperty, {}).setdefault('select', []).append({'id': c.get('id', ''), 'label': c.get('displayname', '')})


            entity['properties'] = sorted(entity.get('properties', {}).values(), key=itemgetter('ordinal'))

            for p in entity['properties']:
                p['values'] = sorted(p.get('values', {}).values(), key=itemgetter('ordinal'))

        if limit == 1:
            return entities[0]

        return entities

    def __get_id_list(self, entity_id=None, search=None, entity_definition_id=None, limit=None):
        """
        Get list of Entity IDs. entity_id, entity_definition_id and user_id can be single ID or list of IDs.

        """
        sql = 'SELECT DISTINCT entity.id AS id FROM property_definition, property, entity, relationship WHERE property.property_definition_id = property_definition.id AND entity.id = property.entity_id AND relationship.entity_id = entity.id'

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

        if self.user_id:
            sql += ' AND relationship.related_entity_id IN (%s) AND relationship.type IN (\'viewer\', \'editor\', \'owner\')' % ','.join(map(str, self.user_id))
        else:
            sql += ' AND entity.public = 1 AND property_definition.public = 1'


        sql += ' ORDER BY entity.created DESC'

        if limit != None:
            sql += ' LIMIT %d' % limit

        sql += ';'
        # logging.info(sql)

        items = self.db.query(sql)
        if not items:
            return []
        return [x.id for x in items]

    def __get_properties(self, entity_id=None):
        """
        Get Entity properties. entity_id can be single ID or list of IDs.

        """
        if not entity_id:
            return

        if type(entity_id) is not list:
            entity_id = [entity_id]

        if self.user_id:
            public = ''
        else:
            public = 'AND entity.public = 1 AND property_definition.public = 1'

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
                property.value_reference                        AS value_reference,
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
            %(public)s
            AND entity.id IN (%(idlist)s)
            ORDER BY
                entity_definition.id,
                entity.created DESC
        """ % {'language': self.language, 'public': public, 'idlist': ','.join(map(str, entity_id))}
        # logging.info(sql)

        items = {}
        for row in self.db.query(sql):
            #Entity
            items.setdefault('item_%s' % row.entity_id, {})['definition_id'] = row.entity_definition_id
            items.setdefault('item_%s' % row.entity_id, {})['id'] = row.entity_id
            items.setdefault('item_%s' % row.entity_id, {})['gae_key'] = row.entity_gaekey
            items.setdefault('item_%s' % row.entity_id, {})['label'] = row.entity_label
            items.setdefault('item_%s' % row.entity_id, {})['label_plural'] = row.entity_label_plural
            items.setdefault('item_%s' % row.entity_id, {})['description'] = row.entity_description
            items.setdefault('item_%s' % row.entity_id, {})['created'] = row.entity_created
            items.setdefault('item_%s' % row.entity_id, {})['displayname'] = row.entity_displayname
            items.setdefault('item_%s' % row.entity_id, {})['displayinfo'] = row.entity_displayinfo
            items.setdefault('item_%s' % row.entity_id, {})['displaytable'] = row.entity_displaytable
            items.setdefault('item_%s' % row.entity_id, {})['file_count'] = 0
            items.setdefault('item_%s' % row.entity_id, {})['is_public'] = True if row.entity_public == 1 else False

            #Property
            items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['id'] = row.property_id
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
                db_value = row.value_string
                value = row.value_string
            elif row.property_datatype == 'text':
                db_value = row.value_text
                value = row.value_text
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
                db_value = row.value_reference
                value = row.value_reference
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

        for key, value in items.iteritems():
            items[key] = dict(items[key].items() + self.__get_displayfields(value).items())
            items[key]['displaypicture'] = self.__get_picture_url(value['id'])

        return items.values()

    def __get_displayfields(self, entity_dict):
        """
        Returns Entity displayname, displayinfo, displaytable fields.

        """
        result = {}
        for displayfield in ['displayname', 'displayinfo', 'displaytable']:
            result[displayfield] = entity_dict[displayfield] if entity_dict[displayfield] else ''
            for data_property in findTags(entity_dict[displayfield], '@', '@'):
                result[displayfield] = result[displayfield].replace('@%s@' % data_property, ', '.join(['%s' % x['value'] for x in entity_dict.get('properties', {}).get(data_property, {}).get('values', {}).values()]))

        result['displaytable_labels'] = entity_dict['displaytable'] if entity_dict['displaytable'] else ''
        for data_property in findTags(entity_dict['displaytable'], '@', '@'):
            result['displaytable_labels'] = result['displaytable_labels'].replace('@%s@' % data_property, entity_dict.get('properties', {}).get(data_property, {}).get('label', ''))

        result['displaytable'] = result['displaytable'].split('|') if result['displaytable'] else None
        result['displaytable_labels'] = result['displaytable_labels'].split('|') if result['displaytable_labels'] else None

        # logging.info(result.get('displaytable_labels'))
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
        # logging.info(sql)

        return self.db.query(sql)

    def get_relatives(self, entity_id=None, relation_type=None, limit=None):
        """
        Get Entity relatives.

        """
        if not entity_id:
            return

        if type(entity_id) is not list:
            entity_id = [entity_id]

        sql = 'SELECT DISTINCT relationship.type, relationship.related_entity_id AS id FROM entity, relationship, relationship AS rights WHERE relationship.related_entity_id = entity.id AND rights.entity_id = relationship.related_entity_id AND relationship.entity_id IN (%s)' % ','.join(map(str, entity_id))

        if self.user_id:
            sql += ' AND rights.related_entity_id IN (%s) AND rights.type IN (\'viewer\', \'editor\', \'owner\')' % ','.join(map(str, self.user_id))
        else:
            sql += ' AND entity.public = 1'

        if relation_type:
            if type(relation_type) is not list:
                relation_type = [relation_type]
            sql += ' AND relationship.type IN (%s)' % ','.join(['\'%s\'' % x for x in relation_type])

        sql += ' ORDER BY entity.id DESC'

        if limit:
            sql += ' LIMIT %d' % limit

        sql += ';'
        # logging.info(sql)

        items = {}
        for item in self.db.query(sql):
            ent = self.__get_properties(item.id)
            if not ent:
                continue
            ent = ent[0]
            items.setdefault(item.type, {}).setdefault('%s' % ent.get('label_plural', ''), []).append(ent)
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
        # logging.info(sql)

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
        sql = """
            SELECT
            id,
            %(language)s_label AS label,
            %(language)s_label_plural AS label_plural,
            %(language)s_description AS description,
            %(language)s_menu AS menugroup
            FROM
            entity_definition
            WHERE id = %(id)s
            LIMIT 1
        """  % {'language': self.language, 'id': entity_definition_id}
        # logging.info(sql)

        return self.db.get(sql)

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
            relationship
            WHERE relationship.related_entity_definition_id = entity_definition.id
            AND relationship.type = 'allowed_child'
            AND relationship.entity_id = %(id)s
        """  % {'language': self.language, 'id': entity_id}
        # logging.info(sql)

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
            relationship
            WHERE relationship.related_entity_definition_id = entity_definition.id
            AND relationship.type='allowed_child'
            AND relationship.entity_definition_id = (SELECT entity_definition_id FROM entity WHERE id = %(id)s)
        """  % {'language': self.language, 'id': entity_id}
        # logging.info(sql)

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
            relationship
            WHERE entity.entity_definition_id = entity_definition.id
            AND relationship.entity_id = entity.id
            AND relationship.type IN ('viewer', 'editor', 'owner')
            AND entity_definition.estonian_menu IS NOT NULL
            AND relationship.related_entity_id IN (%(user_id)s)
            ORDER BY
            entity_definition.estonian_menu,
            entity_definition.estonian_label;
        """ % {'language': self.language, 'user_id': ','.join(map(str, self.user_id))}
        # logging.info(sql)

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
            user.picture
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
    return format % {'year': date.year, 'month': date.month, 'day': date.day, 'hour': date.hour, 'minute': date.minute}


def findTags(s, beginning, end):
    """
    Finds and returns list of tags from string.

    """
    if not s:
        return []
    return re.compile('%s(.*?)%s' % (beginning, end), re.DOTALL).findall(s)
