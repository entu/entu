# task.py
import torndb
import json
from datetime import datetime
from formula import *


class ETask():


    def __init__(self, connenction_params):
        self.customers = {}
        self.db = torndb.Connection(
            host     = connenction_params.database_host,
            database = connenction_params.database_name,
            user     = connenction_params.database_user,
            password = connenction_params.database_password,
        )
        self.cg_sql = EQuery().customers(connenction_params.customergroup)

    def reload_customers(self):
        self.customers = {}
        for c in self.db.query(self.cg_sql):
            self.customers.setdefault(c.entity, {}).setdefault(c.property, []).append(c.value)

    def evaluate_formula(self, db, formula_property_row):
        frm = Formula(db, formula_property_row.id, formula_property_row.entity_id, formula_property_row.value_formula)
        frm_value = ''.join(frm.evaluate())
        if frm_value != formula_property_row.value_display:
            sql = "UPDATE property SET value_display = %s WHERE id = %s;"
            db.execute(sql, frm_value, formula_property_row.id)

    def update_related_formulas(self, db, property_row, fpath):
        # print property_row
        if property_row.id in fpath:
            print "Recursion detected"
            print property_row
            print json.dumps(fpath)
            raw_input('Press enter')
            return
        # if len(fpath)>0:
        #     print property_row
        #     print json.dumps(fpath)
        #     raw_input('Press enter')
        fpath.append(property_row.id)
        qresult = db.query(EQuery().related_formulas(property_row, 'parent'))
        if len(qresult) > 0:
            for formula_property_row in qresult:
                self.evaluate_formula(db, formula_property_row)
                self.update_related_formulas(db, formula_property_row, fpath=fpath)

        qresult = db.query(EQuery().related_formulas(property_row, 'child'))
        if len(qresult) > 0:
            for formula_property_row in qresult:
                self.evaluate_formula(db, formula_property_row)
                self.update_related_formulas(db, formula_property_row, fpath=fpath)

        qresult = db.query(EQuery().related_formulas(property_row, 'self'))
        if len(qresult) > 0:
            for formula_property_row in qresult:
                self.evaluate_formula(db, formula_property_row)
                self.update_related_formulas(db, formula_property_row, fpath=fpath)

        qresult = db.query(EQuery().related_formulas(property_row, 'back-referencing'))
        if len(qresult) > 0:
            for formula_property_row in qresult:
                self.evaluate_formula(db, formula_property_row)
                self.update_related_formulas(db, formula_property_row, fpath=fpath)

class EQuery():

    def customers(self, customergroup = '0'):
        if customergroup == '':
            customergroup = '0'
        return """
        SELECT DISTINCT
                cp.entity_id AS entity,
                cpd.dataproperty AS property,
                IF(
                    cpd.datatype='decimal',
                    cp.value_decimal,
                    IF(
                        cpd.datatype='integer',
                        cp.value_integer,
                        IF(
                            cpd.datatype='file',
                            cp.value_file,
                            cp.value_string
                        )
                    )
                ) AS value
        FROM entity cge
        LEFT JOIN relationship r ON r.entity_id = cge.id
        LEFT JOIN entity ce ON ce.id = r.related_entity_id
        LEFT JOIN property cp ON cp.entity_id = ce.id
        LEFT JOIN property_definition cpd ON cpd.keyname = cp.property_definition_keyname
        WHERE cge.entity_definition_keyname = 'customergroup'
          AND cge.is_deleted = 0
          AND ce.entity_definition_keyname = 'customer' AND ce.is_deleted = 0
          AND r.relationship_definition_keyname = 'child' AND r.is_deleted = 0
          AND cp.is_deleted = 0
          AND ('%s' = '0' OR cge.id IN (%s))
        ORDER BY cp.entity_id, cpd.ordinal;
        """ % (customergroup, customergroup)

    def fresh_properties(self, lim, first_second, last_second = None):
        #   These queries should be rewritten to retrieve specific columns only not select *
        # and grouped for max(o_date)
        if last_second:
            return """
                SELECT *
                FROM
                (SELECT pd.dataproperty, pd.datatype, p.created AS o_date, p.*
                  FROM property p
                  LEFT JOIN property_definition pd ON pd.keyname = p.property_definition_keyname
                  LEFT JOIN entity e on e.id = p.entity_id
                 WHERE p.created >= '%(first_second)s' and p.created <= '%(last_second)s'
                 AND p.is_deleted = 0
                 AND e.is_deleted = 0
                 ORDER BY o_date
                ) cr
                UNION SELECT * FROM
                (SELECT pd.dataproperty, pd.datatype, p.deleted AS o_date, p.*
                  FROM property p
                  LEFT JOIN property_definition pd ON pd.keyname = p.property_definition_keyname
                  LEFT JOIN entity e on e.id = p.entity_id
                 WHERE p.deleted >= '%(first_second)s' and p.deleted <= '%(last_second)s'
                 AND p.is_deleted = 1
                 AND e.is_deleted = 0
                 ORDER BY o_date
                ) de
                ORDER BY o_date
                """ % {'first_second': first_second, 'last_second': last_second}
        else:
            return """
                SELECT *
                FROM
                (SELECT pd.dataproperty, pd.datatype, p.created AS o_date, p.*
                  FROM property p
                  LEFT JOIN property_definition pd ON pd.keyname = p.property_definition_keyname
                  LEFT JOIN entity e on e.id = p.entity_id
                 WHERE p.created > '%(date)s'
                 AND p.is_deleted = 0
                 AND e.is_deleted = 0
                 ORDER BY o_date
                 LIMIT %(limit)s
                ) cr
                UNION SELECT * FROM
                (SELECT pd.dataproperty, pd.datatype, p.deleted AS o_date, p.*
                  FROM property p
                  LEFT JOIN property_definition pd ON pd.keyname = p.property_definition_keyname
                  LEFT JOIN entity e on e.id = p.entity_id
                 WHERE p.deleted > '%(date)s'
                 AND p.is_deleted = 1
                 AND e.is_deleted = 0
                 ORDER BY o_date
                 LIMIT %(limit)s
                ) de
                ORDER BY o_date
                 LIMIT %(limit)s
                """ % {'limit': lim, 'date': first_second}

    def related_formulas(self, property_row, direction):
        sql = {}
        # print property_row
        # Parent formula properties with ".child." in its value_formula (SLQ is NOT tested)
        sql['parent'] = """
            SELECT pd.dataproperty, p_formula.*
            FROM relationship r
            LEFT JOIN entity e_formula ON e_formula.id = r.entity_id
                      AND e_formula.is_deleted = 0
            LEFT JOIN property p_formula ON p_formula.entity_id = e_formula.id
                      AND p_formula.is_deleted = 0
            RIGHT JOIN property_definition pd ON p_formula.property_definition_keyname = pd.keyname
                      AND ( p_formula.value_formula LIKE concat('%%%%.child.',pd.entity_definition_keyname,'.%s}%%%%')
                        OR  p_formula.value_formula LIKE '%%%%.child.*.%s}%%%%'
                          )
            WHERE r.related_entity_id = %s
              AND r.relationship_definition_keyname = 'child'
              AND pd.formula = 1
              AND r.is_deleted = 0
              AND ifnull(p_formula.changed, "%s") < "%s";
        """ % (property_row.dataproperty, property_row.dataproperty, property_row.entity_id, datetime.min, property_row.created)

        # Child formula properties (SLQ is NOT tested)
        sql['child'] = """
            SELECT pd.dataproperty, p_formula.*
            FROM relationship r
            LEFT JOIN entity e_formula ON e_formula.id = r.related_entity_id
                      AND e_formula.is_deleted = 0
            LEFT JOIN property p_formula ON p_formula.entity_id = e_formula.id
                      AND p_formula.is_deleted = 0
            RIGHT JOIN property_definition pd ON p_formula.property_definition_keyname = pd.keyname
                      AND ( p_formula.value_formula LIKE concat('%%%%.-child.',pd.entity_definition_keyname,'.%s}%%%%')
                        OR  p_formula.value_formula LIKE '%%%%.-child.*.%s}%%%%'
                          )
            WHERE r.entity_id = %s
              AND r.relationship_definition_keyname = 'child'
              AND pd.formula = 1
              AND r.is_deleted = 0
              AND ifnull(p_formula.changed, "%s") < "%s";
        """ % (property_row.dataproperty, property_row.dataproperty, property_row.entity_id, datetime.min, property_row.created)

        # Self referencing formula properties (SLQ is NOT tested)
        sql['self'] = """
            SELECT pd.dataproperty, p_formula.id, p_formula.entity_id, p_formula.value_formula, p_formula.value_display
            FROM entity e_formula
            LEFT JOIN property p_formula ON p_formula.entity_id = e_formula.id
                        AND p_formula.is_deleted = 0
                        AND p_formula.value_formula LIKE concat('%%%%{self.%s}%%%%')
            RIGHT JOIN property_definition pd ON pd.keyname = p_formula.property_definition_keyname
            WHERE e_formula.is_deleted = 0
              AND pd.formula = 1
              AND e_formula.id = %s
              AND ifnull(p_formula.changed, "%s") < "%s";
        """ % (property_row.dataproperty, property_row.entity_id, datetime.min, property_row.created)

        # Back-referencing formula properties (SLQ is tested)
        sql['back-referencing'] = """
            SELECT pd2.dataproperty, p_formula.id, p_formula.entity_id, p_formula.value_formula, p_formula.value_display
            FROM property p_reference
            RIGHT JOIN property_definition pd_reference ON pd_reference.keyname = p_reference.property_definition_keyname
                        AND pd_reference.datatype = 'reference'
            LEFT JOIN entity e_formula ON e_formula.id = p_reference.value_reference
                        AND e_formula.is_deleted = 0
            LEFT JOIN property p_formula ON p_formula.entity_id = e_formula.id
                        AND p_formula.is_deleted = 0
                        AND p_formula.value_formula LIKE concat('%%%%.-', pd_reference.dataproperty, '.%%%%')
            RIGHT JOIN property_definition pd2 ON pd2.keyname = p_formula.property_definition_keyname
            WHERE p_reference.is_deleted = 0
              AND pd2.formula = 1
              AND p_reference.entity_id = %s
              AND ifnull(p_formula.changed, "%s") < "%s";
        """ % (property_row.entity_id, datetime.min, property_row.created)

        return sql[direction]


    # def get_displayproperties(self, entity_id, language):
    #     return """
    #     SELECT pd.dataproperty k, p.value_display v, ifnull(p.value_file,'') AS f, ifnull(p.value_reference,'') AS r, IF(t.value IS NULL, '', 1 + length(substring_index(t.value, concat('@',pd.dataproperty,'@'),1)) - length(REPLACE(substring_index(t.value, concat('@',pd.dataproperty,'@'),1),'|',''))) AS t
    #     FROM property p
    #     LEFT JOIN property_definition pd ON pd.keyname = p.property_definition_keyname
    #     LEFT JOIN translation t ON pd.entity_definition_keyname = t.entity_definition_keyname AND t.field = 'displaytable' AND t.value LIKE concat('%%%%@',pd.dataproperty,'@%%%%')
    #     WHERE p.entity_id = %(entity_id)s
    #     AND p.is_deleted = 0
    #     AND ifnull(p.language,'%(language)s') = '%(language)s'
    #     ORDER BY pd.ordinal, p.id;
    #     """ % {'entity_id': entity_id, 'language': language}


    # def get_displayfields(self, entity_id, language):
    #     return """
    #     SELECT "search" AS field, LEFT(GROUP_CONCAT(p.value_display ORDER BY pd.ordinal, p.id SEPARATOR ' '), 2000) AS "displayfield"
    #     FROM property AS p
    #     LEFT JOIN  property_definition AS pd ON pd.keyname = p.property_definition_keyname
    #     WHERE p.entity_id = %(entity_id)s
    #     AND ifnull(p.language, '%(language)s') = '%(language)s'
    #     AND p.is_deleted = 0
    #     AND pd.is_deleted = 0
    #     AND pd.search = 1
    # UNION
    #     SELECT t.field, GROUP_CONCAT(IF (numbers.n MOD 2 = 1, SUBSTRING_INDEX(SUBSTRING_INDEX(t.value, '@', numbers.n), '@', -1), ifnull(p.value_display,''))  ORDER BY numbers.n SEPARATOR '') AS displayfield
    #     FROM
    #     (
    #     SELECT 1 AS n
    #     UNION SELECT 2 AS n
    #     UNION SELECT 3 AS n
    #     UNION SELECT 4 AS n
    #     UNION SELECT 5 AS n
    #     UNION SELECT 6 AS n
    #     UNION SELECT 7 AS n
    #     UNION SELECT 8 AS n
    #     UNION SELECT 9 AS n
    #     UNION SELECT 10 AS n
    #     UNION SELECT 11 AS n
    #     UNION SELECT 12 AS n
    #     UNION SELECT 13 AS n
    #     UNION SELECT 14 AS n
    #     UNION SELECT 15 AS n
    #     UNION SELECT 16 AS n
    #     UNION SELECT 17 AS n
    #     UNION SELECT 18 AS n
    #     ) AS numbers
    #     INNER JOIN translation t ON CHAR_LENGTH(t.value)-CHAR_LENGTH(REPLACE(t.value, '@', '')) >= numbers.n-1
    #     INNER JOIN entity e ON t.entity_definition_keyname = e.entity_definition_keyname
    #      LEFT JOIN property p ON p.entity_id = e.id AND p.property_definition_keyname = concat(e.entity_definition_keyname, '-', SUBSTRING_INDEX(SUBSTRING_INDEX(t.value, '@', numbers.n), '@', -1))
    #     WHERE e.id = %(entity_id)s
    #     AND e.is_deleted = 0
    #     AND ifnull(p.is_deleted,0) = 0
    #     AND t.field IN ('displayname','displayinfo','sort')
    #     AND ifnull(t.`language`,'%(language)s') = '%(language)s'
    #     GROUP BY t.field
    #     """ % {'entity_id': entity_id, 'language': language}

    # def catchup_value_display(self):
    #     return """
    #     UPDATE property p
    #     LEFT JOIN property_definition pd ON pd.keyname = p.property_definition_keyname
    #     SET p.value_display =
    #       IF (pd.datatype = 'string', p.value_string,
    #         IF (pd.datatype = 'decimal', round(p.value_decimal,2),
    #           IF (pd.datatype = 'integer', p.value_integer,
    #             IF (pd.datatype = 'date', date_format(p.value_datetime,'%%Y-%%m-%%d'),
    #               IF (pd.datatype = 'datetime', date_format(p.value_datetime,'%%Y-%%m-%%d %%H:%%i'),
    #                 IF (pd.datatype = 'boolean', if(p.value_boolean = 1, 'True', 'False'),
    #                   IF (pd.datatype = 'counter', p.value_counter,
    #                     IF (pd.datatype = 'counter-value', p.value_string,
    #                       IF (pd.datatype = 'file', (SELECT `filename` FROM `file` WHERE id = p.value_file),
    #                         IF (pd.datatype = 'text', p.value_text,
    #                           IF (pd.datatype = 'secret', p.value_string, '')))))))))))
    #     WHERE p.is_deleted = 0
    #     AND pd.is_deleted = 0
    #     AND pd.datatype IN ('boolean','counter','counter-value','decimal','date','datetime','file','integer','string','text','secret')
    #     AND pd.formula = 0;
    #     """

    # def catchup_entity_search(self):
    #     return """
    #     UPDATE entity_info AS ei
    #     LEFT JOIN
    #     (
    #     SELECT p.entity_id, %s, ifnull(p.language, %s) AS "language", LEFT(GROUP_CONCAT(p.value_display ORDER BY pd.ordinal, p.id SEPARATOR ' '), 2000) AS "displayfield"
    #     FROM property AS p
    #     LEFT JOIN  property_definition AS pd ON pd.keyname = p.property_definition_keyname
    #     WHERE ifnull(p.language, %s) = %s
    #     AND p.is_deleted = 0
    #     AND pd.is_deleted = 0
    #     AND pd.search = 1
    #     GROUP BY p.entity_id
    #     ) foo ON ei.entity_id = foo.entity_id AND ei.language = foo.language
    #     SET ei.search_it = foo.displayfield
    #     WHERE ei.language = %s;
    #     """

    # def catchup_entity_display(self):
    #     return """
    #     UPDATE entity_info AS ei
    #     LEFT JOIN
    #     (
    #     SELECT e.id AS entity_id, %s AS "language", t.field, GROUP_CONCAT(IF (numbers.n MOD 2 = 1, SUBSTRING_INDEX(SUBSTRING_INDEX(t.value, '@', numbers.n), '@', -1), ifnull(p.value_display,'')) ORDER BY numbers.n SEPARATOR '') AS displayfield
    #     FROM
    #     ( SELECT 1 AS n UNION SELECT 2 AS n UNION SELECT 3 AS n UNION SELECT 4 AS n UNION SELECT 5 AS n UNION SELECT 6 AS n UNION SELECT 7 AS n UNION SELECT 8 AS n UNION SELECT 9 AS n UNION SELECT 10 AS n UNION SELECT 11 AS n UNION SELECT 12 AS n UNION SELECT 13 AS n UNION SELECT 14 AS n UNION SELECT 15 AS n UNION SELECT 16 AS n UNION SELECT 17 AS n UNION SELECT 18 AS n UNION SELECT 19 AS n UNION SELECT 20 AS n
    #     ) AS numbers
    #     INNER JOIN translation t ON CHAR_LENGTH(t.value)-CHAR_LENGTH(REPLACE(t.value, '@', '')) >= numbers.n-1
    #     INNER JOIN entity e ON t.entity_definition_keyname = e.entity_definition_keyname
    #      LEFT JOIN property p ON p.entity_id = e.id AND p.property_definition_keyname = concat(e.entity_definition_keyname, '-', SUBSTRING_INDEX(SUBSTRING_INDEX(t.value, '@', numbers.n), '@', -1))
    #     WHERE e.is_deleted = 0
    #     AND ifnull(p.is_deleted,0) = 0
    #     AND t.field IN ('sort','displayname','displayinfo')
    #     AND ifnull(t.language, %s) = %s
    #     AND ifnull(p.language, %s) = %s
    #     GROUP BY e.id, t.field
    #     ) foo ON ei.entity_id = foo.entity_id AND ei.language = foo.language
    #     SET ei.sort_it = IF(foo.field = 'sort', foo.displayfield, ei.sort_it)
    #       , ei.displayname = IF(foo.field = 'displayname', foo.displayfield, ei.displayname)
    #       , ei.displayinfo = IF(foo.field = 'displayinfo', foo.displayfield, ei.displayinfo)
    #     WHERE ei.language = %s;
    #     """

    # def catchup_value_reference(self):
    #     return """
    #     UPDATE property p
    #     LEFT JOIN entity_info ei ON ei.entity_id = p.value_reference AND ei.language = ifnull(p.language, %s)
    #     LEFT JOIN entity ep ON ep.id = p.entity_id
    #     LEFT JOIN entity er ON er.id = p.value_reference
    #     SET p.value_display = ei.displayname
    #     WHERE p.is_deleted = 0
    #     AND ep.is_deleted = 0
    #     AND er.is_deleted = 0;
    #     """





def formatDatetime(date, format='%(day)02d.%(month)02d.%(year)d %(hour)02d:%(minute)02d'):
    """
    Formats and returns date as string. Format tags are %(day)02d, %(month)02d, %(year)d, %(hour)02d and %(minute)02d.

    """
    if not date:
        return ''
    return format % {'year': date.year, 'month': date.month, 'day': date.day, 'hour': date.hour, 'minute': date.minute}


