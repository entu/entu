import newrelic.agent
newrelic.agent.initialize()


import os
import re
import time
import torndb

from operator import itemgetter
from datetime import datetime


APP_MYSQL_HOST     = os.getenv('MYSQL_HOST', 'localhost')
APP_MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')
APP_MYSQL_USER     = os.getenv('MYSQL_USER')
APP_MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
APP_CUSTOMERGROUP  = os.getenv('CUSTOMERGROUP')
APP_FULLRUN        = os.getenv('FULLRUN')
APP_VERBOSE        = os.getenv('VERBOSE', 1)


def customers():
    db = torndb.Connection(
        host     = APP_MYSQL_HOST,
        database = APP_MYSQL_DATABASE,
        user     = APP_MYSQL_USER,
        password = APP_MYSQL_PASSWORD,
    )

    sql = """
        SELECT DISTINCT
            e.id AS entity,
            property_definition.dataproperty AS property,
            IF(
                property_definition.datatype='decimal',
                property.value_decimal,
                IF(
                    property_definition.datatype='integer',
                    property.value_integer,
                    IF(
                        property_definition.datatype='file',
                        property.value_file,
                        property.value_string
                    )
                )
            ) AS value
        FROM (
            SELECT
                entity.id,
                entity.entity_definition_keyname
            FROM
                entity,
                relationship
            WHERE relationship.related_entity_id = entity.id
            AND entity.is_deleted = 0
            AND relationship.is_deleted = 0
            AND relationship.relationship_definition_keyname = 'child'
            AND relationship.entity_id IN (%s)
        ) AS e
        LEFT JOIN property_definition ON property_definition.entity_definition_keyname = e.entity_definition_keyname AND property_definition.is_deleted = 0
        LEFT JOIN property ON property.property_definition_keyname = property_definition.keyname AND property.entity_id = e.id AND property.is_deleted = 0;
    """ % APP_CUSTOMERGROUP

    customers = {}
    for c in db.query(sql):
        if c.property in ['database-host', 'database-name', 'database-user', 'database-password', 'language']:
            customers.setdefault(c.entity, {})[c.property] = c.value

    return sorted(customers.values(), key=itemgetter('database-name'))




class Maintenance():
    def __init__(self, db_host, db_name, db_user, db_pass, language, hours, speed):
        self.db_host = db_host
        self.db_name = db_name
        self.db_user = db_user
        self.db_pass = db_pass
        self.db = torndb.Connection(
            host     = db_host,
            database = db_name,
            user     = db_user,
            password = db_pass,
        )

        self.language = language
        self.speed = speed
        self.time = 0
        self.formulas = 0

        self.hours = hours
        self.changed_entities = []

        # get changed entities
        if APP_FULLRUN:
            sql = """
                SELECT id FROM entity;
            """
        else:
            sql = """
                      SELECT id AS id FROM entity WHERE deleted >= DATE_SUB(NOW(), INTERVAL %(hours)s HOUR)
                UNION SELECT id AS id FROM entity WHERE created >= DATE_SUB(NOW(), INTERVAL %(hours)s HOUR)
                UNION SELECT entity_id AS id FROM property WHERE deleted >= DATE_SUB(NOW(), INTERVAL %(hours)s HOUR)
                UNION SELECT entity_id AS id FROM property WHERE created >= DATE_SUB(NOW(), INTERVAL %(hours)s HOUR)
                UNION SELECT entity_id AS id FROM relationship WHERE deleted >= DATE_SUB(NOW(), INTERVAL %(hours)s HOUR)
                UNION SELECT entity_id AS id FROM relationship WHERE created >= DATE_SUB(NOW(), INTERVAL %(hours)s HOUR)
                UNION SELECT related_entity_id AS id FROM relationship WHERE deleted >= DATE_SUB(NOW(), INTERVAL %(hours)s HOUR)
                UNION SELECT related_entity_id AS id FROM relationship WHERE created >= DATE_SUB(NOW(), INTERVAL %(hours)s HOUR);
            """ % { 'hours': self.hours }

        for r in self.db.query(sql):
            self.changed_entities.append(r.id)

        self.changed_entities = list(set([x for x in self.changed_entities if x]))


    def echo(self, msg='', level=0):
        if int(APP_VERBOSE) >= level:
            msg = '%s -%s- %s' % (datetime.now(), self.db_name, msg)
            print msg.encode('UTF-8')


    def set_sort(self):
        #remove unused sort string
        self.db.execute("""
            UPDATE entity e
            LEFT JOIN translation t ON t.entity_definition_keyname = e.entity_definition_keyname AND t.field = 'sort'
            SET e.sort = NULL
            WHERE e.sort IS NOT NULL
            AND t.field IS NULL;
        """)

        #generate numbers subselect
        fields_count = self.db.query("""
            SELECT MAX(LENGTH(value) - LENGTH(REPLACE(value, '@', '')) + 1) AS fields
            FROM translation
            WHERE IFNULL(language, %s) = %s;
        """, self.language, self.language)[0].fields
        numbers_list = []
        for f in range(1, fields_count + 1):
            numbers_list.append('SELECT %s AS n' % f)
        numbers_sql = ' UNION '.join(numbers_list)

        #generate entity select
        sql = """
            SELECT
                x.id,
                GROUP_CONCAT(x.val ORDER BY n SEPARATOR '') AS val
            FROM (
                SELECT
                    e.id,
                    n.n,
                    GROUP_CONCAT(IF(n.n MOD 2 = 1, SUBSTRING_INDEX(SUBSTRING_INDEX(t.value, '@', n.n), '@', -1), IFNULL(p.value_display, '')) ORDER BY p.value_display SEPARATOR '; ') AS val
                FROM (%(numbers_sql)s) AS n
                INNER JOIN translation AS t ON t.field = 'sort' AND CHAR_LENGTH(t.value) - CHAR_LENGTH(REPLACE(t.value, '@', '')) >= n.n - 1 AND IFNULL(t.language, '%(language)s') = '%(language)s'
                INNER JOIN (
                    SELECT e.id, e.entity_definition_keyname
                    FROM entity AS e
                    WHERE e.id IN (%(changed_entities)s)
                ) AS e ON e.entity_definition_keyname = t.entity_definition_keyname
                LEFT JOIN property AS p ON p.entity_id = e.id AND p.is_deleted = 0 AND p.property_definition_keyname = CONCAT(e.entity_definition_keyname, '-', SUBSTRING_INDEX(SUBSTRING_INDEX(t.value, '@', n.n), '@', -1)) AND IFNULL(p.language, '%(language)s') = '%(language)s'
                GROUP BY id, n
            ) AS x
            GROUP BY x.id;
        """ % {'numbers_sql': numbers_sql, 'language': self.language, 'changed_entities': ','.join(map(str, self.changed_entities))}

        rows = self.db.query(sql)

        count = len(rows)
        if not rows:
            self.echo('no changed entities', 1)
            return

        self.echo('checking %s entities for sort' % count, 2)

        i = 0
        for r in rows:
            if not r.id:
                continue
            if not self.db.get('SELECT id FROM entity WHERE LEFT(IFNULL(sort, \'\'), 100) <> LEFT(%s, 100) AND id = %s AND is_deleted = 0 LIMIT 1;', r.val, r.id):
                continue
            i += 1
            self.echo('#%s %s' % (r.id, r.val), 2)
            self.db.execute('UPDATE entity SET sort = LEFT(%s, 100) WHERE IFNULL(sort, \'\') <> LEFT(%s, 100) AND id = %s AND is_deleted = 0;', r.val, r.val, r.id)

        self.echo('updated %s entities for sort' % i, 2)


    def set_reference_properties(self):
        #generate numbers subselect
        fields_count = self.db.query("""
            SELECT MAX(LENGTH(value) - LENGTH(REPLACE(value, '@', '')) + 1) AS fields
            FROM translation
            WHERE IFNULL(language, %s) = %s;
        """, self.language, self.language)[0].fields
        numbers_list = []
        for f in range(1, fields_count + 1):
            numbers_list.append('SELECT %s AS n' % f)
        numbers_sql = ' UNION '.join(numbers_list)

        #generate entity select
        sql = """
            SELECT
                x.id,
                GROUP_CONCAT(x.val ORDER BY n SEPARATOR '') AS val
            FROM (
                SELECT
                    e.id,
                    n.n,
                    GROUP_CONCAT(IF(n.n MOD 2 = 1, SUBSTRING_INDEX(SUBSTRING_INDEX(t.value, '@', n.n), '@', -1), IFNULL(p.value_display, '')) ORDER BY p.value_display SEPARATOR '; ') AS val
                FROM (%(numbers_sql)s) AS n
                INNER JOIN translation AS t ON t.field = 'displayname' AND CHAR_LENGTH(t.value) - CHAR_LENGTH(REPLACE(t.value, '@', '')) >= n.n - 1 AND IFNULL(t.language, '%(language)s') = '%(language)s'
                INNER JOIN (
                    SELECT e.id, e.entity_definition_keyname
                    FROM entity AS e
                    WHERE e.id IN (
                        SELECT value_reference
                        FROM property
                        WHERE value_reference IN (%(changed_entities)s)
                    )
                ) AS e ON e.entity_definition_keyname = t.entity_definition_keyname
                LEFT JOIN property AS p ON p.entity_id = e.id AND p.is_deleted = 0 AND p.property_definition_keyname = CONCAT(e.entity_definition_keyname, '-', SUBSTRING_INDEX(SUBSTRING_INDEX(t.value, '@', n.n), '@', -1)) AND IFNULL(p.language, '%(language)s') = '%(language)s'
                GROUP BY id, n
            ) AS x
            GROUP BY x.id;
        """ % {'numbers_sql': numbers_sql, 'language': self.language, 'changed_entities': ','.join(map(str, self.changed_entities))}

        rows = self.db.query(sql)

        count = len(rows)
        if not rows:
            self.echo('no changed reference properties', 1)
            return

        self.echo('checking %s reference properties' % count, 2)

        i = 0
        for r in rows:
            if not r.id:
                continue
            if not self.db.get('SELECT id FROM property WHERE LEFT(IFNULL(value_display, \'\'), 500) <> LEFT(%s, 500) AND value_reference = %s AND is_deleted = 0 LIMIT 1;', r.val, r.id):
                continue
            i += 1
            self.echo('#%s %s' % (r.id, r.val), 2)
            self.db.execute('UPDATE property SET value_display = LEFT(%s, 500) WHERE IFNULL(value_display, \'\') <> LEFT(%s, 500) AND value_reference = %s AND is_deleted = 0;', r.val, r.val, r.id)

        self.echo('updated %s reference properties' % i, 2)


    def set_formula_properties(self):
        start = time.time()

        sql = """
            SELECT
                p.id,
                p.value_display,
                pd.dataproperty
            FROM
                entity AS e,
                property AS p,
                property_definition AS pd
            WHERE p.entity_id = e.id
            AND pd.keyname = p.property_definition_keyname
            AND e.id IN (
                SELECT id FROM entity WHERE is_deleted = 0 AND id IN (%(changed_entities)s)
                UNION SELECT entity_id FROM property WHERE is_deleted = 0 AND value_reference IN (%(changed_entities)s)
                UNION SELECT value_reference FROM property WHERE is_deleted = 0 AND entity_id IN (%(changed_entities)s) AND value_reference > 0
                UNION SELECT entity_id FROM relationship WHERE is_deleted = 0 AND relationship_definition_keyname = 'child' AND related_entity_id IN (%(changed_entities)s)
                UNION SELECT related_entity_id FROM relationship WHERE is_deleted = 0 AND relationship_definition_keyname = 'child' AND entity_id IN (%(changed_entities)s)
            )
            AND e.is_deleted = 0
            AND p.is_deleted = 0
            AND pd.is_deleted = 0
            AND pd.formula = 1
            ORDER BY p.id;
        """ % {'changed_entities': ','.join(map(str, self.changed_entities))}

        rows = self.db.query(sql)
        count = len(rows)

        if not rows:
            self.echo('no changed formulas', 1)
            return
        self.echo('checking %s formulas (~%s min)' % (count, round(float(count) * float(self.speed) / 60.0, 1)), 1)

        i = 0
        for r in rows:
            formula = self.__calculate_formula(r.id)
            if r.value_display == formula:
                continue
            i += 1
            if r.value_display:
                self.echo('#%s %s "%s" => "%s"' % (r.id, r.dataproperty, r.value_display, formula), 2)
            else:
                self.echo('#%s %s "%s"' % (r.id, r.dataproperty, formula), 2)

            self.db.execute('UPDATE property SET value_display = LEFT(%s, 500) WHERE id = %s;', formula, r.id)

        self.time = time.time() - start
        if self.time == 0:
            self.time = 0.0001

        self.formulas = count
        self.echo('updated %s formulas (%s fps)' % (i, round(float(m.formulas) / float(m.time), 1)), 1)


    def __calculate_formula(self, property_id):
        if not property_id:
            return

        # get formula property
        formula_property = self.db.get("""
            SELECT
                entity_id,
                REPLACE(REPLACE(REPLACE(value_formula, '.*.', '..'), '.-child.', '.parent.'), '.-', '.referrer.') AS formula
            FROM property
            WHERE id = %s
            AND entity_id > 0
            AND IFNULL(value_formula, '') != ''
            LIMIT 1;
        """, property_id)

        if not formula_property:
            return

        operators   = ['+', '*', '/'] #['+', '-', '*', '/']
        functions   = ['SUM', 'COUNT', 'AVERAGE', 'MIN', 'MAX', 'UNIQUE']
        fields      = []
        fieldvalues = {}

        formula_string = formula_property.formula
        entity_id      = formula_property.entity_id

        # get fields from formula string
        for formula in re.findall('{(.*?)}', formula_string):
            for component in re.split('\\%s' % '|\\'.join(operators), ''.join(formula.split())):
                if not component:
                    continue
                if component[-1] != ')':
                    fields.append(component)
                else:
                    for function in functions:
                        for c in re.findall('%s\((.*?)\)' % function, component):
                            fields.append(c)

        # get field values
        for f in list(set([x for x in fields if x.find('.') > 0])):
            fieldvalues[f] = self.__get_formula_value(entity_id, f)

        # calculate functions and make string
        for formula in re.findall('{(.*?)}', formula_string):
            pure_formula = ''.join(formula.split())
            for function in functions:
                for c in re.findall('%s\((.*?)\)' % function, pure_formula):
                    values = fieldvalues[c]
                    try:
                        function_result  = ''
                        if function == 'SUM':
                            function_result = sum(map(float, [x for x in values if x]))
                        if function == 'COUNT':
                            function_result = len(values)
                        if function == 'AVERAGE' and [x for x in values if x]:
                            function_result = sum(map(float, [x for x in values if x])) / len(values)
                        if function == 'MIN':
                            function_result = min(values)
                        if function == 'MAX':
                            function_result = max(values)
                        if function == 'UNIQUE':
                            function_result = list(set(values))
                    except Exception, e:
                        function_result  = u'%s_ERROR(%s "%s")' % (function, e, values)

                    if type(function_result) is list:
                        function_result = '; '.join([u'%s' % x for x in sorted(function_result)])
                    pure_formula = pure_formula.replace(u'%s(%s)' % (function, c), '%s' % function_result)

            for f_key, f_values in fieldvalues.iteritems():
                pure_formula = pure_formula.replace(f_key, '; '.join([u'%s' % x for x in sorted(f_values)]))

            # try:
            #     pure_formula = u'%s' % eval(pure_formula, {'__builtins__': None})
            # except Exception, e:
            #     pass

            formula_string = formula_string.replace(u'{%s}' % formula, pure_formula)

        return formula_string


    def __get_formula_value(self, entity_id, formula):
        formula_fields = formula.split('.')

        if formula_fields[0] != 'self':
            try:
                entity_id = int(formula_fields[0])
            except Exception, e:
                return []

        sql_select = 'e.id AS value_display'
        sql_from   = ['entity AS e']
        sql_where  = ['e.is_deleted = 0']
        reference_entity_field = None

        if formula_fields[1] in ['parent', 'child', 'referrer']:
            if formula_fields[1] == 'parent':
                sql_from.append('relationship AS r')
                sql_where.append('r.entity_id = e.id')
                sql_where.append('r.relationship_definition_keyname = \'child\'')
                sql_where.append('r.is_deleted = 0')
                sql_where.append('r.related_entity_id = %s' % entity_id)
            elif formula_fields[1] == 'child':
                sql_from.append('relationship AS r')
                sql_where.append('r.related_entity_id = e.id')
                sql_where.append('r.relationship_definition_keyname = \'child\'')
                sql_where.append('r.is_deleted = 0')
                sql_where.append('r.entity_id = %s' % entity_id)
            elif formula_fields[1] == 'referrer':
                sql_from.append('property AS r')
                sql_where.append('r.entity_id = e.id')
                sql_where.append('r.is_deleted = 0')
                sql_where.append('r.value_reference = %s' % entity_id)
            if formula_fields[2]:
                sql_where.append('e.entity_definition_keyname = \'%s\'' % formula_fields[2])
            try:
                dataproperty = formula_fields[3]
            except Exception as e:
                print e
                print self.db_name
                print formula_fields
        else:
            sql_where.append('e.id = %s' % entity_id)
            dataproperty = formula_fields[1]
            if len(formula_fields) > 2:
                reference_entity_field = formula_fields[2]

        if dataproperty != 'id':
            if reference_entity_field:
                if reference_entity_field == 'id':
                    sql_select = 'p.value_reference as value_display'
                    sql_from.append('property AS p')
                    sql_from.append('property_definition AS pd')
                    sql_where.append('p.entity_id = e.id')
                    sql_where.append('pd.keyname = p.property_definition_keyname')
                    sql_where.append('p.is_deleted = 0')
                    sql_where.append('pd.is_deleted = 0')
                    sql_where.append('pd.dataproperty = \'%s\'' % dataproperty)
                else:
                    sql_select = 'rep.value_display'
                    sql_from.append('property AS p')
                    sql_from.append('property_definition AS pd')
                    sql_from.append('property AS rep')
                    sql_from.append('property_definition AS repd')
                    sql_where.append('p.entity_id = e.id')
                    sql_where.append('pd.keyname = p.property_definition_keyname')
                    sql_where.append('rep.entity_id = p.value_reference')
                    sql_where.append('repd.keyname = rep.property_definition_keyname')
                    sql_where.append('p.is_deleted = 0')
                    sql_where.append('pd.is_deleted = 0')
                    sql_where.append('rep.is_deleted = 0')
                    sql_where.append('repd.is_deleted = 0')
                    sql_where.append('pd.dataproperty = \'%s\'' % dataproperty)
                    sql_where.append('repd.dataproperty = \'%s\'' % reference_entity_field)
            else:
                if formula_fields[1] == '_created':
                    sql_select = 'e.created as value_display'
                else:
                    sql_select = 'p.value_display'
                    sql_from.append('property AS p')
                    sql_from.append('property_definition AS pd')
                    sql_where.append('p.entity_id = e.id')
                    sql_where.append('pd.keyname = p.property_definition_keyname')
                    sql_where.append('p.is_deleted = 0')
                    sql_where.append('pd.is_deleted = 0')
                    sql_where.append('pd.dataproperty = \'%s\'' % dataproperty)

        sql = """
            SELECT %(sql_select)s
            FROM %(sql_from)s
            WHERE 1 = 1
            AND %(sql_where)s;
        """ % {
            'sql_select': sql_select,
            'sql_from': ' , '.join(sql_from),
            'sql_where': ' AND '.join(sql_where),
        }

        result = []
        for v in self.db.query(sql):
            result.append(v.value_display)

        return result




total_count = 0.0001
total_time  = 0.0000

while True:

    print '\n\n%s START' % datetime.now()

    for c in customers():
        start = time.time()

        # if c.get('database-name') != 'saksa':
        #     continue

        m = Maintenance(
            db_host = c.get('database-host'),
            db_name = c.get('database-name'),
            db_user = c.get('database-user'),
            db_pass = c.get('database-password'),
            language = c.get('language'),
            hours = 2,
            speed = total_time / total_count
        )

        m.echo('start', 1)

        if m.changed_entities:
            m.set_formula_properties()
            m.set_reference_properties()
            m.set_sort()

        else:
            m.echo('entities not changed', 1)

        m.echo('end (%ss)\n' % round(time.time() - start, 1), 1)

        total_count += m.formulas
        total_time += m.time

        time.sleep(1)
