import logging

from main.helper import *

class Entity2():
    @property
    def __user_id(self):
        if not self.current_user:
            return None
        if not self.current_user.id:
            return None
        return self.current_user.id


    @property
    def __language(self):
        return self.get_user_locale().code


    def get_entity_definitions(self, definition_id=None):

        definition_sql = ''
        if definition_id:
            definition_sql = 'AND e.id = %s' % definition_id

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
            definition_where = """
                AND e.entity_definition_keyname = '%s'
            """ % definition

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
                    SELECT entity_id
                    FROM property
                    WHERE value_reference IN (%s)
                    AND is_deleted = 0
                )
                """ % ', '.join(referred_to_entity_id)

        query_where = ''
        if query:
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
                        and p.value_display LIKE '%%%%%s%%%%'
                    )
                """ % q

        if self.__user_id:
            entity_sql = """
                SELECT e.id, e.entity_definition_keyname, IFNULL(e.sort, CONCAT('   ', 1000000000000 - e.id)) AS sort
                FROM entity AS e
                WHERE e.is_deleted = 0
                AND e.sharing IN ('domain', 'public')
                %(definition_where)s
                %(parent_where)s
                %(referrer_where)s
                %(query_where)s
                UNION SELECT e.id, e.entity_definition_keyname, IFNULL(e.sort, CONCAT('   ', 1000000000000 - e.id)) AS sort
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
                SELECT e.id, e.entity_definition_keyname, IFNULL(e.sort, CONCAT('   ', 1000000000000 - e.id)) AS sort
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
                x.definition,
                x.field,
                GROUP_CONCAT(x.val ORDER BY n SEPARATOR '') AS val
            FROM (
                SELECT
                    e.id,
                    e.sort,
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
            entities.setdefault(r.get('id'), {})[r.get('field')] = r.get('val')

        return {
            'entities': entities.values(),
            'count': entity_count if entity_count else len(entities.values()),
        }


    def get_entity_picture_url(self, entity_id):
        f = self.db.get("""
            SELECT
                e.entity_definition_keyname AS definition,
                (
                    SELECT p.value_file
                    FROM
                        property AS p,
                        property_definition AS pd
                    WHERE pd.keyname = p.property_definition_keyname
                    AND p.is_deleted = 0
                    AND p.value_file > 0
                    AND p.entity_id = e.id
                    AND pd.entity_definition_keyname = e.entity_definition_keyname
                    AND pd.is_deleted = 0
                    AND pd.dataproperty = 'photo'
                    ORDER BY p.id
                    LIMIT 1
                ) AS value_file
            FROM entity AS e
            WHERE e.id = %s
            AND e.is_deleted = 0
            LIMIT 1;
        """, entity_id)
        if not f:
            return
        if f.value_file:
            return '/api2/file-%s' % f.value_file
        elif f.definition in ['audiovideo', 'book', 'methodical', 'periodical', 'textbook', 'workbook']:
            return '/photo-by-isbn?entity=%s' % entity_id
        elif f.definition == 'person':
            return 'https://secure.gravatar.com/avatar/%s?d=wavatar&s=150' % (hashlib.md5(str(entity_id)).hexdigest())
        else:
            return 'https://secure.gravatar.com/avatar/%s?d=identicon&s=150' % (hashlib.md5(str(entity_id)).hexdigest())
