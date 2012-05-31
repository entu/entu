from tornado import database
from tornado.options import options

import logging
import hashlib


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


def formatDatetime(date, format='%(day)d.%(month)d.%(year)d %(hour)d:%(minute)d'):
    """
    Formats and returns date as string. Format tags are %(day)d, %(month)d, %(year)d, %(hour)d and %(minute)d.

    """
    return format % {'year': date.year, 'month': date.month, 'day': date.day, 'hour': date.hour, 'minute': date.minute}


class Entity():
    """
    Entity class. user_id can be single ID or list of IDs.
    """
    def __init__(self, only_public=True, user_id=None, language='estonian'):
        self.db             = connection()

        self.only_public    = only_public
        self.language       = language
        self.user_id        = user_id

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
        sql = 'SELECT STRAIGHT_JOIN DISTINCT bubble.id AS id FROM property_definition, property, bubble, relationship WHERE property.property_definition_id = property_definition.id AND bubble.id = property.bubble_id AND relationship.bubble_id = bubble.id'
        if entity_id:
            if type(entity_id) is not list:
                entity_id = [entity_id]
            sql += ' AND bubble.id IN (%s)' % ','.join(map(str, entity_id))

        if search:
            for s in search.split(' '):
                sql += ' AND value_string LIKE \'%%%%%s%%%%\'' % s

        if self.only_public == True:
            sql += ' AND property_definition.public = 1 AND bubble.public = 1'

        if entity_definition:
            if type(entity_definition) is not list:
                entity_definition = [entity_definition]
            sql += ' AND bubble.bubble_definition_id IN (%s)' % ','.join(map(str, entity_definition))

            sql += ' AND relationship.related_bubble_id IN (%s) AND relationship.type IN (\'viewer\', \'editor\', \'owner\')' % ','.join(map(str, self.user_id))

        sql += ' ORDER BY bubble.id'

        if limit:
            sql += ' LIMIT %d' % limit

        sql += ';'
        # logging.info(sql)

        items = self.db.query(sql)
        if not items:
            return []
        return [x.id for x in items]

    def __get_properties(self, entity_id):
        """
        Get Entity properties. entity_id can be single ID or list of IDs.

        """
        if not entity_id:
            return []

        if type(entity_id) is not list:
            entity_id = [entity_id]

        if self.only_public == True:
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

    def get_picture_url(self, entity_id):
        """
        Returns Entity picture.

        """
        return 'http://www.gravatar.com/avatar/%s?d=identicon' % (hashlib.md5(str(entity_id)).hexdigest())

    def get_menu(self):
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
            AND relationship.related_bubble_id IN (%(user_id)s)
            ORDER BY
            bubble_definition.estonian_menu,
            bubble_definition.estonian_label;
        """ % {'language': self.language, 'user_id': ','.join(map(str, self.user_id))}
        # logging.info(sql)

        menu = {}
        for m in self.db.query(sql):
            menu.setdefault(m.menugroup, []).append({'id': m.id, 'title': m.item})
        return menu

    def get_file(self, file_id):
        """
        Returns file object. File properties are id, file, filename.

        """

        publicsql = 'AND property_definition.public = 1' if self.only_public == True else ''
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
            property.bubble_id AS id,
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
