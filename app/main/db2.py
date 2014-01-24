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
                        and p.value_string LIKE '%%%%%s%%%%'
                    )
                    """ % q

        entity_sql = """
            SELECT e.id, e.entity_definition_keyname, IFNULL(e.sort, CONCAT('   ', 1000000000000 - e.id)) AS sort
            FROM entity AS e
            WHERE e.is_deleted = 0
            AND e.sharing IN ('domain', 'public')
            %(definition_where)s
            %(parent_where)s
            %(referrer_where)s
            %(query_where)s
        """ % {'definition_where': definition_where, 'parent_where': parent_where, 'referrer_where': referrer_where, 'query_where': query_where}

        if self.current_user:
            entity_sql += """
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
            """ % {'definition_where': definition_where, 'parent_where': parent_where, 'referrer_where': referrer_where, 'query_where': query_where, 'user': self.__user_id, 'limit': limit}

        if limit:
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
                    GROUP_CONCAT(IF(n.n MOD 2 = 1, SUBSTRING_INDEX(SUBSTRING_INDEX(t.value, '@', n.n), '@', -1), IFNULL(p.value_string, '')) ORDER BY p.value_string SEPARATOR '; ') AS val
                FROM (%(numbers_sql)s) AS n
                INNER JOIN translation AS t ON CHAR_LENGTH(t.value) - CHAR_LENGTH(REPLACE(t.value, '@', '')) >= n.n - 1 AND IFNULL(t.language, '%(language)s') = '%(language)s'
                INNER JOIN (%(entity_sql)s) AS e ON e.entity_definition_keyname = t.entity_definition_keyname
                LEFT JOIN property AS p ON p.entity_id = e.id AND p.is_deleted = 0 AND p.property_definition_keyname = CONCAT(e.entity_definition_keyname, '-', SUBSTRING_INDEX(SUBSTRING_INDEX(t.value, '@', n.n), '@', -1))
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

        return entities.values()
