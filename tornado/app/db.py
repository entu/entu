from tornado import database
from tornado import locale
from tornado.options import options

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

    def get(self, ids_only=False, entity_id=None, search=None, entity_definition=None, limit=None):
        """
        If ids_only==True, then returns list of Entity IDs. Else returns list of Entities (with properties) as dictionary. entity_id and entity_definition can be single ID or list of IDs.

        """
        ids = self.__get_id_list(entity_id=entity_id, search=search, entity_definition=entity_definition, limit=limit)

        if ids_only:
            return ids

        return self.__get_properties(entity_id=ids)

    def __get_id_list(self, entity_id=None, search=None, entity_definition=None, limit=None):
        """
        Get list of Entity IDs. entity_id, entity_definition and user_id can be single ID or list of IDs.

        """
        sql = 'SELECT DISTINCT entity.id AS id FROM property_definition, property, entity, relationship WHERE property.property_definition_id = property_definition.id AND entity.id = property.entity_id AND relationship.entity_id = entity.id'

        if entity_id:
            if type(entity_id) is not list:
                entity_id = [entity_id]
            sql += ' AND entity.id IN (%s)' % ','.join(map(str, entity_id))

        if search:
            for s in search.split(' '):
                sql += ' AND value_string LIKE \'%%%%%s%%%%\'' % s

        if entity_definition:
            if type(entity_definition) is not list:
                entity_definition = [entity_definition]
            sql += ' AND entity.entity_definition_id IN (%s)' % ','.join(map(str, entity_definition))

        if self.user_id:
            sql += ' AND relationship.related_entity_id IN (%s) AND relationship.type IN (\'viewer\', \'editor\', \'owner\')' % ','.join(map(str, self.user_id))
        else:
            sql += ' AND entity.public = 1 AND property_definition.public = 1'


        sql += ' ORDER BY entity.id'

        if limit:
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
            public = 'AND property_definition.public = 1 AND entity.public = 1'

        sql = """
            SELECT
                entity_definition.id                            AS entity_definition_id,
                entity.id                                       AS entity_id,
                entity_definition.%(language)s_label            AS entity_label,
                entity_definition.%(language)s_label_plural     AS entity_label_plural,
                entity_definition.%(language)s_description      AS entity_description,
                entity.created                                  AS entity_created,
                entity_definition.%(language)s_displayname      AS entity_displayname,
                entity_definition.%(language)s_displayinfo      AS entity_displayinfo,
                entity_definition.%(language)s_displaytable     AS entity_displaytable,
                property_definition.%(language)s_fieldset       AS property_fieldset,
                property_definition.%(language)s_label          AS property_label,
                property_definition.%(language)s_label_plural   AS property_label_plural,
                property_definition.%(language)s_description    AS property_description,
                property_definition.datatype                    AS property_datatype,
                property_definition.dataproperty                AS property_dataproperty,
                property_definition.multilingual                AS property_multilingual,
                property_definition.multiplicity                AS property_multiplicity,
                property_definition.ordinal                     AS property_ordinal,
                property.id                                     AS value_id,
                property.value_string                           AS value_string,
                property.value_text                             AS value_text,
                property.value_integer                          AS value_integer,
                property.value_decimal                          AS value_decimal,
                property.value_boolean                          AS value_boolean,
                property.value_datetime                         AS value_datetime,
                property.value_reference                        AS value_reference,
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
                entity.id
        """ % {'language': self.language, 'public': public, 'idlist': ','.join(map(str, entity_id))}
        # logging.info(sql)

        items = {}
        for row in self.db.query(sql):
            if not row.value_string and not row.value_text and not row.value_integer and not row.value_decimal and not row.value_boolean and not row.value_datetime and not row.value_reference and not row.value_file:
                continue

            #Entity
            items.setdefault('item_%s' % row.entity_id, {})['id'] = row.entity_id
            items.setdefault('item_%s' % row.entity_id, {})['label'] = row.entity_label
            items.setdefault('item_%s' % row.entity_id, {})['label_plural'] = row.entity_label_plural
            items.setdefault('item_%s' % row.entity_id, {})['description'] = row.entity_description
            items.setdefault('item_%s' % row.entity_id, {})['created'] = row.entity_created
            items.setdefault('item_%s' % row.entity_id, {})['displayname'] = row.entity_displayname
            items.setdefault('item_%s' % row.entity_id, {})['displayinfo'] = row.entity_displayinfo
            items.setdefault('item_%s' % row.entity_id, {})['displaytable'] = row.entity_displaytable

            #Property
            items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['label'] = row.property_label
            items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['label_plural'] = row.property_label_plural
            items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['description'] = row.property_description
            items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['datatype'] = row.property_datatype
            items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['dataproperty'] = row.property_dataproperty
            items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['multilingual'] = row.property_multilingual
            items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['multiplicity'] = row.property_multiplicity
            items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {})['ordinal'] = row.property_ordinal

            #Value
            if row.property_datatype in ['string', 'select']:
                value = row.value_string
            elif row.property_datatype == 'text':
                value = row.value_text
            elif row.property_datatype == 'integer':
                value = row.value_integer
            elif row.property_datatype == 'float':
                value = row.value_decimal
            elif row.property_datatype == 'date':
                value = formatDatetime(row.value_datetime, '%(day)d.%(month)d.%(year)d')
            elif row.property_datatype == 'datetime':
                value = formatDatetime(row.value_datetime)
            elif row.property_datatype == 'reference':
                value = row.value_reference
            elif row.property_datatype == 'file':
                blobstore = self.db.get('SELECT id, filename, filesize FROM file WHERE id=%s', row.value_file)
                value = blobstore.filename
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {}).setdefault('values', {}).setdefault('value_%s' % row.value_id, {})['file_id'] = blobstore.id
                items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {}).setdefault('values', {}).setdefault('value_%s' % row.value_id , {})['filesize'] = blobstore.filesize
            elif row.property_datatype == 'boolean':
                value = self.user_locale.translate('boolean_true') if row.value_boolean == 1 else self.user_locale.translate('boolean_false')
            elif row.property_datatype == 'counter':
                value = row.value_reference
            else:
                value = 'X'

            items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {}).setdefault('values', {}).setdefault('value_%s' % row.value_id, {})['id'] = row.value_id
            items.setdefault('item_%s' % row.entity_id, {}).setdefault('properties', {}).setdefault('%s' % row.property_dataproperty, {}).setdefault('values', {}).setdefault('value_%s' % row.value_id, {})['value'] = value

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
        return 'http://www.gravatar.com/avatar/%s?d=identicon&s=150' % (hashlib.md5(str(entity_id)).hexdigest())

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

        sql += ' ORDER BY entity.id'

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
        logging.info(sql)

        return self.db.get(sql)

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
            menu.setdefault(m.menugroup, []).append({'id': m.id, 'title': m.item})
        return menu

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


def formatDatetime(date, format='%(day)d.%(month)d.%(year)d %(hour)d:%(minute)d'):
    """
    Formats and returns date as string. Format tags are %(day)d, %(month)d, %(year)d, %(hour)d and %(minute)d.

    """
    return format % {'year': date.year, 'month': date.month, 'day': date.day, 'hour': date.hour, 'minute': date.minute}


def findTags(s, beginning, end):
    """
    Finds and returns list of tags from string.

    """
    if not s:
        return []
    return re.compile('%s(.*?)%s' % (beginning, end), re.DOTALL).findall(s)
