from operator import itemgetter
from PIL import Image
from StringIO import StringIO
from boto.s3.connection import S3Connection
from boto.s3.key import Key

import os
import logging


from main.helper import *


class Entity2():
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


    def get_entity_definitions(self, definition_id=None):

        definition_sql = ''
        if definition_id:
            definition_sql = 'AND e.id = \'%s\'' % definition_id

        sql = """
            SELECT
                e.id AS entity_id,
                NULL AS property_id,
                p.property_definition_keyname AS pdk,
                p.value_string,
                p.value_integer,
                p.value_boolean,
                p.value_reference
            FROM
                entity AS e,
                property AS p
            WHERE p.entity_id = e.id
            AND e.entity_definition_keyname = 'conf-entity'
            AND e.is_deleted = 0
            AND p.is_deleted = 0
            %(definition)s
            AND IFNULL(p.language, '%(language)s') = '%(language)s'
            UNION SELECT
                r.entity_id,
                e.id AS property_id,
                p.property_definition_keyname AS pdk,
                p.value_string,
                p.value_integer,
                p.value_boolean,
                p.value_reference
            FROM
            entity AS e,
            property AS p,
            relationship AS r
            WHERE p.entity_id = e.id
            AND r.related_entity_id = e.id
            AND e.entity_definition_keyname = 'conf-property'
            AND r.relationship_definition_keyname = 'child'
            AND e.is_deleted = 0
            AND p.is_deleted = 0
            AND r.is_deleted = 0
            %(definition)s
            AND IFNULL(p.language, '%(language)s') = '%(language)s'
        """ % {'definition': definition_sql, 'language': self.__language}
        # logging.warning(sql)

        entities = {}
        entity_template = {
            'id': None,
            'keyname': None,
            'ordinal': 0,
            'label': None,
            'label_plural': None,
            'description': None,

            'display_info': None,
            'display_name': None,
            'display_table': None,
            'display_tableheader': None,
            'sort': None,

            'allowed_child_of': None,
            'default_parent': None,
            'optional_parent': None,

            'add_plugin': None,
            'edit_plugin': None,

            'open_after_add': False,

            'properties': [],
        }
        property_template = {
            'classifier': None,
            'createonly': None,
            'keyname': None,
            'datatype': None,
            'defaultvalue': None,
            'description': None,
            'executable': False,
            'fieldset': None,
            'formula': None,
            'label': None,
            'label_plural': None,
            'mandatory': False,
            'multilingual': False,
            'multiplicity': None,
            'ordinal': 0,
            'propagates': None,
            'public': False,
            'readonly': False,
            'search': False,
            'visible': False,
        }
        for r in self.db.query(sql):
            if r.get('entity_id'):
                entities.setdefault(r.get('entity_id'), {})['id'] = r.get('entity_id')
            if r.get('pdk') == 'conf-entity-keyname':
                entities.setdefault(r.get('entity_id'), {})['keyname'] = r.get('value_string')
            if r.get('pdk') == 'conf-entity-ordinal':
                entities.setdefault(r.get('entity_id'), {})['ordinal'] = r.get('value_integer')
            if r.get('pdk') == 'conf-entity-label':
                entities.setdefault(r.get('entity_id'), {})['label'] = r.get('value_string')
            if r.get('pdk') == 'conf-entity-label-plural':
                entities.setdefault(r.get('entity_id'), {})['label_plural'] = r.get('value_string')
            if r.get('pdk') == 'conf-entity-description':
                entities.setdefault(r.get('entity_id'), {})['description'] = r.get('value_string')

            if r.get('pdk') == 'conf-entity-displayname':
                entities.setdefault(r.get('entity_id'), {})['display_name'] = r.get('value_string')
            if r.get('pdk') == 'conf-entity-displayinfo':
                entities.setdefault(r.get('entity_id'), {})['display_info'] = r.get('value_string')
            if r.get('pdk') == 'conf-entity-displaytable':
                entities.setdefault(r.get('entity_id'), {})['display_table'] = r.get('value_string')
            if r.get('pdk') == 'conf-entity-displaytableheader':
                entities.setdefault(r.get('entity_id'), {})['display_tableheader'] = r.get('value_string')
            if r.get('pdk') == 'conf-entity-sort':
                entities.setdefault(r.get('entity_id'), {})['sort'] = r.get('value_string')

            if r.get('pdk') == 'conf-entity-allowed-child-of':
                entities.setdefault(r.get('entity_id'), {}).setdefault('allowed_child_of', []).append(r.get('value_reference'))
            if r.get('pdk') == 'conf-entity-default-parent':
                entities.setdefault(r.get('entity_id'), {}).setdefault('default_parent', []).append(r.get('value_reference'))
            if r.get('pdk') == 'conf-entity-optional-parent':
                entities.setdefault(r.get('entity_id'), {}).setdefault('optional_parent', []).append(r.get('value_reference'))

            if r.get('pdk') == 'conf-entity-add-plugin':
                entities.setdefault(r.get('entity_id'), {}).setdefault('add_plugin', []).append(r.get('value_string'))
            if r.get('pdk') == 'conf-entity-edit-plugin':
                entities.setdefault(r.get('entity_id'), {}).setdefault('edit_plugin', []).append(r.get('value_string'))

            if r.get('pdk') == 'conf-entity-open-after-add':
                entities.setdefault(r.get('entity_id'), {})['open_after_add'] = bool(r.get('value_boolean'))



            if r.get('property_id'):
                entities.setdefault(r.get('entity_id'), {}).setdefault('properties', {}).setdefault(r.get('property_id'), {})['id'] = r.get('property_id')
            if r.get('pdk') == 'conf-property-classifier':
                entities.setdefault(r.get('entity_id'), {}).setdefault('properties', {}).setdefault(r.get('property_id'), {})['classifier'] = r.get('value_string')
            if r.get('pdk') == 'conf-property-dataproperty':
                entities.setdefault(r.get('entity_id'), {}).setdefault('properties', {}).setdefault(r.get('property_id'), {})['keyname'] = r.get('value_string')
            if r.get('pdk') == 'conf-property-datatype':
                entities.setdefault(r.get('entity_id'), {}).setdefault('properties', {}).setdefault(r.get('property_id'), {})['datatype'] = r.get('value_string')
            if r.get('pdk') == 'conf-property-defaultvalue':
                entities.setdefault(r.get('entity_id'), {}).setdefault('properties', {}).setdefault(r.get('property_id'), {})['defaultvalue'] = r.get('value_string')
            if r.get('pdk') == 'conf-property-description':
                entities.setdefault(r.get('entity_id'), {}).setdefault('properties', {}).setdefault(r.get('property_id'), {})['description'] = r.get('value_string')
            if r.get('pdk') == 'conf-property-executable':
                entities.setdefault(r.get('entity_id'), {}).setdefault('properties', {}).setdefault(r.get('property_id'), {})['executable'] = bool(r.get('value_boolean'))
            if r.get('pdk') == 'conf-property-fieldset':
                entities.setdefault(r.get('entity_id'), {}).setdefault('properties', {}).setdefault(r.get('property_id'), {})['fieldset'] = r.get('value_string')
            if r.get('pdk') == 'conf-property-formula':
                entities.setdefault(r.get('entity_id'), {}).setdefault('properties', {}).setdefault(r.get('property_id'), {})['formula'] = bool(r.get('value_boolean'))
            if r.get('pdk') == 'conf-property-label':
                entities.setdefault(r.get('entity_id'), {}).setdefault('properties', {}).setdefault(r.get('property_id'), {})['label'] = r.get('value_string')
            if r.get('pdk') == 'conf-property-label-plural':
                entities.setdefault(r.get('entity_id'), {}).setdefault('properties', {}).setdefault(r.get('property_id'), {})['label_plural'] = r.get('value_string')
            if r.get('pdk') == 'conf-property-mandatory':
                entities.setdefault(r.get('entity_id'), {}).setdefault('properties', {}).setdefault(r.get('property_id'), {})['mandatory'] = bool(r.get('value_boolean'))
            if r.get('pdk') == 'conf-property-multilingual':
                entities.setdefault(r.get('entity_id'), {}).setdefault('properties', {}).setdefault(r.get('property_id'), {})['multilingual'] = bool(r.get('value_boolean'))
            if r.get('pdk') == 'conf-property-multiplicity':
                entities.setdefault(r.get('entity_id'), {}).setdefault('properties', {}).setdefault(r.get('property_id'), {})['multiplicity'] = r.get('value_integer')
            if r.get('pdk') == 'conf-property-ordinal':
                entities.setdefault(r.get('entity_id'), {}).setdefault('properties', {}).setdefault(r.get('property_id'), {})['ordinal'] = r.get('value_integer')
            if r.get('pdk') == 'conf-property-propagates':
                entities.setdefault(r.get('entity_id'), {}).setdefault('properties', {}).setdefault(r.get('property_id'), {})['propagates'] = r.get('value_string')
            if r.get('pdk') == 'conf-property-public':
                entities.setdefault(r.get('entity_id'), {}).setdefault('properties', {}).setdefault(r.get('property_id'), {})['public'] = bool(r.get('value_boolean'))
            if r.get('pdk') == 'conf-property-readonly':
                entities.setdefault(r.get('entity_id'), {}).setdefault('properties', {}).setdefault(r.get('property_id'), {})['readonly'] = bool(r.get('value_boolean'))
            if r.get('pdk') == 'conf-property-search':
                entities.setdefault(r.get('entity_id'), {}).setdefault('properties', {}).setdefault(r.get('property_id'), {})['search'] = bool(r.get('value_boolean'))
            if r.get('pdk') == 'conf-property-visible':
                entities.setdefault(r.get('entity_id'), {}).setdefault('properties', {}).setdefault(r.get('property_id'), {})['visible'] = bool(r.get('value_boolean'))

        entities2 = {}
        for e_id, e in entities.iteritems():
            properties2 = {}
            for p_id, p in e.get('properties', {}).iteritems():
                properties2[p.get('keyname', p_id)] = dict(property_template.items() + p.items())
            e['properties'] = properties2
            entities2[e.get('keyname', e_id)] = dict(entity_template.items() + e.items())
        return entities2



    def get_tag_cloud(self, definition=None, limit=None):
        limit = int(limit) if int(limit) > 0 else 0
        return self.db.query("""
            SELECT value_display AS "Tag",
                   count(1) AS "Count",
                   log(count(1)) AS "Log"
            FROM
              (SELECT p.value_display
               FROM property p
               LEFT JOIN entity e ON e.id = p.entity_id
               WHERE p.property_definition_keyname = %s
                 AND p.value_display IS NOT NULL
                 AND e.is_deleted = 0
                 AND p.is_deleted = 0
                 AND e.sharing = 'public') foo
            GROUP BY value_display
            ORDER BY count(1) DESC LIMIT %s;
        """, definition, limit)


    def get_entities_info(self, entity_id=None, definition=None, parent_entity_id=None, referred_to_entity_id=None, query=None, limit=None, page=None):
        #generate numbers subselect
        fields_count = self.db.query("""
            SELECT MAX(LENGTH(value) - LENGTH(REPLACE(value, '@', '')) + 1) AS fields
            FROM translation
            WHERE IFNULL(language, %s) = %s;
        """, self.__language, self.__language)[0].fields
        numbers_list = []
        for f in range(1, fields_count + 1):
            numbers_list.append('SELECT %s AS n' % f)
        numbers_sql = ' UNION '.join(numbers_list)

        #generate entity select
        definition_where = ''
        if definition:
            if type(definition) is not list:
                definition = [definition]
            definition_where = """
                    AND e.entity_definition_keyname IN (%s)
                """ % ', '.join(['\'%s\'' % x for x in definition])

        parent_where = ''
        if parent_entity_id:
            if type(parent_entity_id) is not list:
                parent_entity_id = [parent_entity_id]
            parent_where = """
                AND e.id IN (
                    SELECT related_entity_id
                    FROM relationship
                    WHERE entity_id IN (%s)
                    AND is_deleted = 0
                    AND relationship_definition_keyname = 'child'
                )
                """ % ', '.join(parent_entity_id)

        referrer_where = ''
        if referred_to_entity_id:
            if type(referred_to_entity_id) is not list:
                referred_to_entity_id = [referred_to_entity_id]
            referrer_where = """
                AND e.id IN (
                    SELECT property.entity_id
                    FROM property, property_definition
                    WHERE property_definition.keyname = property.property_definition_keyname
                    AND property.value_reference IN (%s)
                    AND property_definition.dataproperty NOT IN ('entu-created-by', 'entu-changed-by')
                    AND property.is_deleted = 0
                )
                """ % ', '.join(referred_to_entity_id)

        query_where = ''
        if query:
            if self.__user_id:
                for q in StrToList(query):
                    query_where += """
                        AND e.id IN (
                            SELECT p.entity_id
                            FROM
                                property AS p,
                                property_definition AS pd
                            WHERE pd.keyname = p.property_definition_keyname
                            AND pd.search = 1
                            AND p.is_deleted = 0
                            AND pd.is_deleted = 0
                            AND p.value_display LIKE '%%%%%s%%%%'
                        )
                    """ % q
            else:
                for q in StrToList(query):
                    query_where += """
                        AND e.id IN (
                            SELECT p.entity_id
                            FROM
                                property AS p,
                                property_definition AS pd
                            WHERE pd.keyname = p.property_definition_keyname
                            AND pd.search = 1
                            AND p.is_deleted = 0
                            AND pd.is_deleted = 0
                            AND pd.public = 1
                            AND p.value_display LIKE '%%%%%s%%%%'
                        )
                    """ % q

        if self.__user_id:
            entity_sql = """
                SELECT e.id, e.entity_definition_keyname, IFNULL(e.sort, CONCAT('   ', 1000000000000 - e.id)) AS sort, e.changed, UNIX_TIMESTAMP(e.changed) AS changed_ts
                FROM entity AS e
                WHERE e.is_deleted = 0
                AND e.sharing IN ('domain', 'public')
                %(definition_where)s
                %(parent_where)s
                %(referrer_where)s
                %(query_where)s
                UNION SELECT e.id, e.entity_definition_keyname, IFNULL(e.sort, CONCAT('   ', 1000000000000 - e.id)) AS sort, e.changed, UNIX_TIMESTAMP(e.changed) AS changed_ts
                FROM entity AS e, relationship AS r
                WHERE r.entity_id = e.id
                AND e.is_deleted = 0
                %(definition_where)s
                %(parent_where)s
                %(referrer_where)s
                %(query_where)s
                AND r.is_deleted = 0
                AND r.relationship_definition_keyname IN ('viewer', 'expander', 'editor', 'owner')
                AND r.related_entity_id = %(user)s
            """ % {'definition_where': definition_where, 'parent_where': parent_where, 'referrer_where': referrer_where, 'query_where': query_where, 'user': self.__user_id}
        else:
            entity_sql = """
                SELECT e.id, e.entity_definition_keyname, IFNULL(e.sort, CONCAT('   ', 1000000000000 - e.id)) AS sort, e.changed, UNIX_TIMESTAMP(e.changed) AS changed_ts
                FROM entity AS e
                WHERE e.is_deleted = 0
                AND e.sharing = 'public'
                %(definition_where)s
                %(parent_where)s
                %(referrer_where)s
                %(query_where)s
            """ % {'definition_where': definition_where, 'parent_where': parent_where, 'referrer_where': referrer_where, 'query_where': query_where}

        entity_count = None
        if limit:
            entity_count = self.db.get('SELECT COUNT(*) AS entity_count FROM (%s) AS x' % entity_sql).entity_count

            limit = int(limit) if int(limit) > 0 else 0
            if not page:
                page = 1
            page = int(page) if int(page) > 1 else 1
            offset = (page - 1) * limit

            entity_sql += """
                ORDER BY sort
                LIMIT %s, %s
            """ % (offset, limit)

        #get info
        sql = """
            SELECT
                x.id,
                x.sort,
                x.changed,
                x.changed_ts,
                x.definition,
                x.field,
                GROUP_CONCAT(x.val ORDER BY n SEPARATOR '') AS val
            FROM (
                SELECT
                    e.id,
                    e.sort,
                    e.changed,
                    e.changed_ts,
                    e.entity_definition_keyname AS definition,
                    t.field,
                    n.n,
                    GROUP_CONCAT(IF(n.n MOD 2 = 1, SUBSTRING_INDEX(SUBSTRING_INDEX(t.value, '@', n.n), '@', -1), IFNULL(p.value_display, '')) ORDER BY p.value_display SEPARATOR '; ') AS val
                FROM (%(numbers_sql)s) AS n
                INNER JOIN translation AS t ON CHAR_LENGTH(t.value) - CHAR_LENGTH(REPLACE(t.value, '@', '')) >= n.n - 1 AND IFNULL(t.language, '%(language)s') = '%(language)s'
                INNER JOIN (%(entity_sql)s) AS e ON e.entity_definition_keyname = t.entity_definition_keyname
                LEFT JOIN property AS p ON p.entity_id = e.id AND p.is_deleted = 0 AND p.property_definition_keyname = CONCAT(e.entity_definition_keyname, '-', SUBSTRING_INDEX(SUBSTRING_INDEX(t.value, '@', n.n), '@', -1)) AND IFNULL(p.language, '%(language)s') = '%(language)s'
                GROUP BY id, definition, field, n
            ) AS x
            GROUP BY x.id, x.sort, x.definition, x.field;
        """ % {'numbers_sql': numbers_sql, 'entity_sql': entity_sql, 'language': self.__language}
        # logging.warning(sql)

        entities = {}
        for r in self.db.query(sql):

            if not r.get('val'):
                continue
            entities.setdefault(r.get('id'), {})['id'] = r.get('id')
            entities.setdefault(r.get('id'), {})['definition'] = r.get('definition')
            entities.setdefault(r.get('id'), {})['sort'] = r.get('sort')
            entities.setdefault(r.get('id'), {})['changed'] = r.get('changed')
            entities.setdefault(r.get('id'), {})['changed_ts'] = r.get('changed_ts')
            entities.setdefault(r.get('id'), {})[r.get('field')] = r.get('val')

        return {
            'entities': entities.values(),
            'count': entity_count if entity_count else len(entities.values()),
        }


    def get_entity_picture(self, entity_id):
        f = self.db.get("""
            SELECT
                entity.entity_definition_keyname AS definition,
                file.id AS file_id,
                file.md5,
                file.s3_key
            FROM entity
            LEFT JOIN (
                SELECT
                    p.entity_id,
                    f.id,
                    f.md5,
                    f.s3_key
                FROM
                    property AS p,
                    property_definition AS pd,
                    file AS f
                WHERE pd.keyname = p.property_definition_keyname
                AND f.id = p.value_file
                AND p.is_deleted = 0
                AND p.value_file > 0
                AND p.entity_id = %s
                AND pd.is_deleted = 0
                AND pd.dataproperty = 'photo'
                ORDER BY f.filename
                LIMIT 1
            ) AS file ON file.entity_id = entity.id
            WHERE entity.id = %s
            AND entity.is_deleted = 0
            LIMIT 1;
        """, entity_id, entity_id)
        if not f:
            return

        if not f.md5 and not f.s3_key:
            return

        thumbname = os.path.join('/', 'entu', 'thumbs', self.app_settings('database-name'), '%s' % f.file_id)
        if os.path.isfile(thumbname):
            with open(thumbname, 'r') as myfile:
                filecontent = myfile.read()

        elif f.s3_key:
            try:
                AWS_BUCKET     = self.app_settings('auth-s3', '\n', True).split('\n')[0]
                AWS_ACCESS_KEY = self.app_settings('auth-s3', '\n', True).split('\n')[1]
                AWS_SECRET_KEY = self.app_settings('auth-s3', '\n', True).split('\n')[2]
            except Exception, e:
                return self.json({
                    'error': 'Amazon S3 bucket, key or secret not set!',
                    'time': round(self.request.request_time(), 3),
                }, 400)
            s3_conn   = S3Connection(AWS_ACCESS_KEY, AWS_SECRET_KEY)
            s3_bucket = s3_conn.get_bucket(AWS_BUCKET, validate=False)
            s3_key    = Key(s3_bucket)

            s3_key.key = f.s3_key

            try:
                filecontent = self.save_thumb(Image.open(StringIO(s3_key.get_contents_as_string())), thumbname)
            except Exception, e:
                return self.json({
                    'error': e,
                    'time': round(self.request.request_time(), 3),
                }, 404)

        elif f.md5:
            filename  = os.path.join('/', 'entu', 'files', self.app_settings('database-name'), f.md5[0], f.md5)
            if os.path.isfile(filename):
                filecontent = self.save_thumb(Image.open(filename), thumbname)
            else:
                filecontent = None

        else:
            filecontent = None

        return {'definition': f.definition, 'picture': filecontent}


    def save_thumb(self, im, thumbname, size=(300, 300)):
        try:
            if not os.path.exists(os.path.dirname(thumbname)):
                os.makedirs(os.path.dirname(thumbname))

            if im.size[0] < size[0] and im.size[1] < size[1]:
                aspect = float(im.size[0])/float(im.size[1])
                c = (aspect, 1) if aspect > 0 else (1, aspect)
                im = im.resize((int(im.size[0]*size[0]/im.size[0]*c[0]), int(im.size[1]*size[1]/im.size[1]*c[1])), Image.ANTIALIAS)
            else:
                im.thumbnail(size, Image.ANTIALIAS)

            im_bg = Image.new('RGB', size, (255, 255, 255))
            try:
                im_bg.paste(im, ((size[0] - im.size[0]) / 2, (size[1] - im.size[1]) / 2), im)
            except Exception:
                im_bg.paste(im, ((size[0] - im.size[0]) / 2, (size[1] - im.size[1]) / 2))

            im_bg.save(thumbname, 'JPEG', quality=75)

            with open(thumbname, 'r') as myfile:
                thumb = myfile.read()

            return thumb
        except Exception, e:
            logging.error('%s - %s' % (self.app_settings('database-name'), e))


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

        definitions = {}
        for m in self.db.query(sql):
            definitions.setdefault(m.menu, {})['label'] = m.menu
            definitions.setdefault(m.menu, {}).setdefault('definitions', []).append({
                'keyname': m.definition,
                'label': m.label,
                'label_plural': m.label_plural,
            })

        return sorted(definitions.values(), key=itemgetter('label'))


    def get_public_paths(self):
        """
        Returns public paths with labels

        """

        paths = {}
        for i in self.db.query("""
            SELECT DISTINCT
                keyname,
                public_path,
                (
                    SELECT value
                    FROM translation
                    WHERE language IS NULL or language = %s
                    AND entity_definition_keyname = keyname
                    ORDER BY language DESC
                    LIMIT 1
                ) AS label
            FROM entity_definition
            WHERE public_path IS NOT NULL
            ORDER BY public_path;
        """, self.__language):
            paths[i.public_path] = i.label
        return paths


    def set_entity_right(self, entity_id, related_entity_id, right=None):
        if right and right not in ['viewer', 'expander', 'editor', 'owner']:
            return

        if not self.__user_id:
            return

        if not entity_id:
            return

        if not related_entity_id:
            return

        if not self.db.get("""
                SELECT entity_id
                FROM relationship
                WHERE relationship_definition_keyname = 'owner'
                AND entity_id = %s
                AND related_entity_id = %s
                AND is_deleted = 0
            """,
            entity_id,
            self.__user_id
        ):
            return

        self.db.execute(
            """
                UPDATE relationship SET
                    is_deleted = 1,
                    deleted = NOW(),
                    deleted_by = %s
                WHERE entity_id = %s
                AND related_entity_id = %s
                AND relationship_definition_keyname IN ('viewer', 'expander', 'editor', 'owner');
            """,
            self.__user_id,
            entity_id,
            related_entity_id
        )

        if right:
            self.db.execute(
                """
                    INSERT INTO relationship SET
                    created = NOW(),
                    created_by = %s,
                    entity_id = %s,
                    related_entity_id = %s,
                    relationship_definition_keyname = %s;
                """,
                self.__user_id,
                entity_id,
                related_entity_id,
                right
            )


    def set_tmp_file(self, filename=None, content=None):
        if not filename or not content:
            return

        return self.db.execute_lastrowid('INSERT INTO tmp_file SET filename = %s, file = %s, filesize = LENGTH(file), created = NOW(), created_by = %s;', filename, content, self.__user_id)

    def get_tmp_file(self, filename=None):
        if not filename:
            return

        tmp_file = self.db.get('SELECT filename, file FROM tmp_file WHERE filename = %s LIMIT 1;', filename)

        if not tmp_file:
            return

        return {
            'filename': tmp_file.filename,
            'file': tmp_file.file
        }


    def get_recently_changed(self, timestamp=None, definition=None, limit=50):
        """
        Return entity_id's and changed timestamps
        ordered by timestamps
        from entities of given 'definition'
        that are created/changed/deleted at or after given 'timestamp'.

        If 'timestamp' is not set latest updates will be returned.

        Let the list be no longer than 'limit' different timestamps.
        """

        definition_constraint = ' AND entity_definition_keyname = "%s"' % definition if definition else ''
        timestamp_constraint = ' HAVING timestamp > %s' % timestamp if timestamp else ''
        sort_direction = 'ASC' if timestamp else 'DESC'

        sql = """
            SELECT DISTINCT events.definition AS definition, events.id AS id, dates.action AS action, dates.timestamp AS timestamp
            FROM (
                SELECT DISTINCT 'created at'            AS action,
                                Unix_timestamp(created) AS timestamp
                FROM   entity
                WHERE  is_deleted = 0
                       %(definition_constraint)s
                       %(timestamp_constraint)s
                UNION ALL
                SELECT DISTINCT 'changed at'            AS action,
                                Unix_timestamp(changed) AS timestamp
                FROM   entity
                WHERE  is_deleted = 0
                       %(definition_constraint)s
                       %(timestamp_constraint)s
                UNION ALL
                SELECT DISTINCT 'deleted at'            AS action,
                                Unix_timestamp(deleted) AS timestamp
                FROM   entity
                WHERE  is_deleted = 1
                       %(definition_constraint)s
                       %(timestamp_constraint)s
                ORDER  BY timestamp %(sort_direction)s
                LIMIT %(limit)s
            ) AS dates
            LEFT JOIN (
                SELECT entity_definition_keyname AS definition,
                       id                        AS id,
                       'created at'              AS action,
                       Unix_timestamp(created)   AS timestamp
                FROM   entity
                WHERE  is_deleted = 0
                       %(definition_constraint)s
                       %(timestamp_constraint)s
                UNION ALL
                SELECT entity_definition_keyname AS definition,
                       id                        AS id,
                       'changed at'              AS action,
                       Unix_timestamp(changed)   AS timestamp
                FROM   entity
                WHERE  is_deleted = 0
                       %(definition_constraint)s
                       %(timestamp_constraint)s
                UNION ALL
                SELECT entity_definition_keyname AS definition,
                       id                        AS id,
                       'deleted at'              AS action,
                       Unix_timestamp(deleted)   AS timestamp
                FROM   entity
                WHERE  is_deleted = 1
                       %(definition_constraint)s
                       %(timestamp_constraint)s
            ) AS events
              ON events.timestamp = dates.timestamp
             AND events.action = dates.action
            ORDER BY dates.timestamp;
        """ % {'timestamp_constraint': timestamp_constraint, 'definition_constraint': definition_constraint, 'sort_direction': sort_direction, 'limit': limit}

        return self.db.query(sql)


    def get_parents(self, id=None):
        """
        Return array of parent entity id's
        """
        if not id:
            return

        sql = """
            SELECT ep.id AS id, ep.entity_definition_keyname AS definition
            FROM relationship r
            LEFT JOIN entity e ON e.id = r.related_entity_id
            LEFT JOIN entity ep ON ep.id = r.entity_id
            WHERE r.is_deleted = 0
            AND e.is_deleted = 0
            AND ep.is_deleted = 0
            AND r.relationship_definition_keyname = 'child'
            AND e.id = %(id)s
        """ % {'id': id}

        return self.db.query(sql)


    def get_history_timeframe(self, timestamp=None, limit=10):
        # logging.debug(timestamp)
        # logging.debug(limit)

        if timestamp:
            timestamp = "'" + timestamp + "'"
        else:
            timestamp = 'NOW()'
        sql = """
            SELECT min(tstamp) AS from_ts,
                   max(tstamp) AS to_ts
            FROM
              (SELECT *
               FROM
                 (SELECT tstamp
                  FROM
                    (SELECT r.created AS tstamp
                     FROM relationship r
                     WHERE r.created_by = '%(user_id)s'
                       AND r.created < %(timestamp)s
                     GROUP BY r.created
                     ORDER BY r.created DESC LIMIT %(limit)i) cr
                  UNION SELECT tstamp
                  FROM
                    (SELECT r.deleted AS tstamp
                     FROM relationship r
                     WHERE r.deleted_by = '%(user_id)s'
                       AND r.created < %(timestamp)s
                     GROUP BY r.deleted
                     ORDER BY r.deleted DESC LIMIT %(limit)i) dr
                  UNION SELECT tstamp
                  FROM
                    (SELECT e.created AS tstamp
                     FROM entity e
                     WHERE e.created_by = '%(user_id)s'
                       AND e.created < %(timestamp)s
                     GROUP BY e.created
                     ORDER BY e.created DESC LIMIT %(limit)i) ce
                  UNION SELECT tstamp
                  FROM
                    (SELECT e.deleted AS tstamp
                     FROM entity e
                     WHERE e.deleted_by = '%(user_id)s'
                       AND e.created < %(timestamp)s
                     GROUP BY e.deleted
                     ORDER BY e.deleted DESC LIMIT %(limit)i) de
                  UNION SELECT tstamp
                  FROM
                    (SELECT e.changed AS tstamp
                     FROM entity e
                     WHERE e.changed_by = '%(user_id)s'
                       AND e.changed < %(timestamp)s
                     GROUP BY e.changed
                     ORDER BY e.changed DESC LIMIT %(limit)i) ce) ts
               ORDER BY tstamp DESC LIMIT %(limit)i) AS lts;
            """ % {'user_id': self.__user_id, 'timestamp': timestamp, 'limit': int(limit)}

        # logging.debug(sql)

        result = self.db.get(sql)
        # logging.debug(result)

        return result

    def get_history_events(self, timeframe):
        logging.debug(timeframe)
        from_timestamp = timeframe.from_ts.isoformat()
        to_timestamp = timeframe.to_ts.isoformat()

        sql = """
            SELECT *
            FROM
              (SELECT r.created AS tstamp,
                      'Created relationship' AS "Action",
                      r.id AS "Target",
                      r.relationship_definition_keyname AS "Property",
                      r.entity_id AS "From",
                      r.related_entity_id AS "To"
               FROM relationship r
               WHERE r.created_by = '%(user_id)s'
                 AND r.created BETWEEN '%(from_timestamp)s' AND '%(to_timestamp)s'
               UNION SELECT r.deleted AS tstamp,
                            'Deleted relationship' AS "Action",
                            r.id AS "Target",
                            r.relationship_definition_keyname AS "Property",
                            r.entity_id AS "From",
                            r.related_entity_id AS "To"
               FROM relationship r
               WHERE r.deleted_by = '%(user_id)s'
                 AND r.deleted BETWEEN '%(from_timestamp)s' AND '%(to_timestamp)s'
               UNION SELECT e.created AS tstamp,
                            'Created entity' AS "Action",
                            e.id AS "Target",
                            NULL AS "Property",
                            NULL AS "From",
                            NULL AS "To"
               FROM entity e
               WHERE e.created_by = '%(user_id)s'
                 AND e.created BETWEEN '%(from_timestamp)s' AND '%(to_timestamp)s'
               UNION SELECT e.deleted AS tstamp,
                            'Deleted entity' AS "Action",
                            e.id AS "Target",
                            NULL AS "Property",
                            NULL AS "From",
                            NULL AS "To"
               FROM entity e
               WHERE e.deleted_by = '%(user_id)s'
                 AND e.deleted BETWEEN '%(from_timestamp)s' AND '%(to_timestamp)s'
               UNION SELECT e.changed AS tstamp,
                            'Changed entity' AS "Action",
                            e.id AS "Target",
                            p2.property_definition_keyname AS "Property",
                            p1.value_display AS "From",
                            p2.value_display AS "To"
               FROM entity e
               LEFT JOIN property p1 ON p1.entity_id = e.id
               AND p1.deleted_by = '%(user_id)s'
               AND p1.deleted = e.changed
               LEFT JOIN property p2 ON p2.entity_id = e.id
               AND p2.created_by = '%(user_id)s'
               AND p2.created = e.changed
               WHERE e.changed_by = '%(user_id)s'
                 AND e.changed BETWEEN '%(from_timestamp)s' AND '%(to_timestamp)s') lts
            ORDER BY lts.tstamp DESC ;
            """ % {'user_id': self.__user_id, 'from_timestamp': from_timestamp, 'to_timestamp': to_timestamp}

        # logging.debug(sql)

        result = {}
        for r in self.db.query(sql):
            # logging.debug(r)
            result.setdefault(r.get('tstamp').isoformat(), []).append(r)
        # logging.debug(result)

        return {'from':from_timestamp, 'to':to_timestamp, 'events':sorted(result.items())}
