# task.py
import torndb
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
            self.customers.setdefault(c.entity, {})[c.property] = c.value


    def check_my_formulas(self, db, property_row):
        if property_row.value_formula:
            if property_row.is_deleted == 0:
                # print property_row
                self.revaluate_formulas(db, (property_row,))
                # print EQuery().check_formula(property_row, 'referencing')

        qresult = db.query(EQuery().check_formula(property_row, 'parent'))
        if len(qresult) > 0:
            # print "Have {0} matching parent formulas.".format(len(qresult))
            # print property_row
            self.revaluate_formulas(db, qresult)

        qresult = db.query(EQuery().check_formula(property_row, 'child'))
        if len(qresult) > 0:
            # print "Have {0} matching child formulas.".format(len(qresult))
            # print property_row
            self.revaluate_formulas(db, qresult)

        qresult = db.query(EQuery().check_formula(property_row, 'self'))
        if len(qresult) > 0:
            # print "Have {0} matching self formulas.".format(len(qresult))
            # print property_row
            self.revaluate_formulas(db, qresult)

        qresult = db.query(EQuery().check_formula(property_row, 'back-referencing'))
        if len(qresult) > 0:
            # print "Have {0} matching back-referencing formulas.".format(len(qresult))
            # print property_row
            self.revaluate_formulas(db, qresult)


    def check_my_value_string(self, db, property_row):
        if property_row.is_deleted == 1:
            return

        value_display = ''

        if property_row.datatype in ['string']:
            return
        elif property_row.datatype == 'counter-value':
            return
        elif property_row.datatype in ['text', 'html']:
            value_display = property_row.value_text if property_row.value_text else ''
        elif property_row.datatype == 'integer':
            value_display = property_row.value_integer if property_row.value_integer else ''
        elif property_row.datatype == 'decimal':
            value_display = '%.2f' % property_row.value_decimal if property_row.value_decimal else ''
        elif property_row.datatype == 'date':
            value_display = formatDatetime(property_row.value_datetime, '%(day)02d.%(month)02d.%(year)d')
        elif property_row.datatype == 'datetime':
            value_display = formatDatetime(property_row.value_datetime) if property_row.value_datetime else ''
        elif property_row.datatype == 'reference':
            qresult = db.query(EQuery().get_displayname(property_row))
            if len(qresult) > 0:
                value_display = qresult[0].displayname
                print qresult
        elif property_row.datatype == 'file':
            qresult = db.query('SELECT filename FROM file WHERE id=%s LIMIT 1', property_row.value_file)
            if len(qresult) > 0:
                value_display = qresult[0].filename
        elif property_row.datatype == 'boolean':
            value_display = str(bool(property_row.value_boolean))
        elif property_row.datatype == 'counter':
            value_display = self.db.get('SELECT estonian_label AS label FROM counter WHERE id=%s LIMIT 1' % property_row.value_counter)

        sql = """
            UPDATE property
            SET value_display = '%(value_display)s' WHERE id = %(property_id)i
        """ % {'value_display': value_display, 'property_id': property_row.id}
        try:
            db.execute(sql)
        except:
            print sql


    def revaluate_formulas(self, db, recordset):
        rows_updated = 0
        rows_up_to_date = 0
        # print "----"
        # raw_input("Starting revaluation for {0} rows. Press a key...".format(len(recordset)))

        for formula_property_row in recordset:
            frm = Formula(db, formula_property_row.id, formula_property_row.entity_id, formula_property_row.value_formula)
            frm_value = ''.join(frm.evaluate())
            # print "Old value is: %s" % (formula_property_row.value_string)
            # print "Formula evaluated to: %s" % (frm_value)
            if frm_value != formula_property_row.value_string:
                # print formula_property_row
                rows_updated = rows_updated + 1
                # print "New: '%s' != Old: '%s'. Updating..." % (frm_value, formula_property_row.value_string)

                db.execute("""
                INSERT INTO `property` (`property_definition_keyname`, `entity_id`, `ordinal`, `language`, `value_formula`, `value_string`, `value_text`, `value_integer`, `value_decimal`, `value_boolean`, `value_datetime`, `value_entity`, `value_reference`, `value_file`, `value_counter`, `created`, `created_by`, `changed`, `changed_by`)
                SELECT `property_definition_keyname`, `entity_id`, `ordinal`, `language`, `value_formula`, %s, `value_text`, `value_integer`, `value_decimal`, `value_boolean`, `value_datetime`, `value_entity`, `value_reference`, `value_file`, `value_counter`, `created`, `created_by`, now(), 'maintenance'
                FROM `property` WHERE id = %s;
                """, frm_value, formula_property_row.id)

                sql = """
                    UPDATE property
                    SET deleted = now(), deleted_by = 'maintenance', is_deleted = 1 WHERE id = %s
                """ % (formula_property_row.id)
                db.execute(sql)
                continue
            else:
                rows_up_to_date = rows_up_to_date + 1
                # print "%s equals %s, updating changed and changed_by values" % (frm_value, formula_property_row.value_string)
                # sql = """
                #     UPDATE property
                #     SET changed = now(), changed_by = 'maintenance' WHERE id = %s
                # """ % formula_property_row.id
                # db.execute(sql)

        if rows_updated > 0:
            # raw_input('Revaluation of {0} rows finished.\n=> {1} rows updated\n=> {2} rows were up to date.\nPress a key...'.format(len(recordset), rows_updated, rows_up_to_date))
            print 'Revaluation of {0} rows finished.\n=> {1} rows updated\n=> {2} rows were up to date.'.format(len(recordset), rows_updated, rows_up_to_date)



class EQuery():


    def get_displayname(self, property_row):
        return """
        SELECT e.id AS entity_id, GROUP_CONCAT(IF (numbers.n MOD 2 = 1, SUBSTRING_INDEX(SUBSTRING_INDEX(t.value, '@', numbers.n), '@', -1), ifnull(p.value_string,''))  ORDER BY numbers.n SEPARATOR '') AS displayname
        FROM
        (
        SELECT 1 AS n
        UNION SELECT 2 AS n
        UNION SELECT 3 AS n
        UNION SELECT 4 AS n
        UNION SELECT 5 AS n
        UNION SELECT 6 AS n
        UNION SELECT 7 AS n
        UNION SELECT 8 AS n
        UNION SELECT 9 AS n
        UNION SELECT 10 AS n
        UNION SELECT 11 AS n
        UNION SELECT 12 AS n
        UNION SELECT 13 AS n
        UNION SELECT 14 AS n
        UNION SELECT 15 AS n
        UNION SELECT 16 AS n
        UNION SELECT 17 AS n
        UNION SELECT 18 AS n
        ) AS numbers
        INNER JOIN translation t ON CHAR_LENGTH(t.value)-CHAR_LENGTH(REPLACE(t.value, '@', '')) >= numbers.n-1
        INNER JOIN entity e ON t.entity_definition_keyname = e.entity_definition_keyname
         LEFT JOIN property p ON p.entity_id = e.id AND p.property_definition_keyname = concat(e.entity_definition_keyname, '-', SUBSTRING_INDEX(SUBSTRING_INDEX(t.value, '@', numbers.n), '@', -1))
        WHERE e.id = %(entity_id)s
        AND e.is_deleted = 0
        AND ifnull(p.is_deleted,0) = 0
        AND t.field = 'displayname'
        AND ifnull(t.`language`,'%(language)s') = '%(language)s'
        ORDER BY e.sort, e.id, t.field, numbers.n
        """ % {'entity_id': property_row.value_reference, 'language': property_row.language}


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
                 WHERE p.created >= '%(first_second)s' and p.created <= '%(last_second)s'
                 ORDER BY o_date
                ) cr
                UNION SELECT * FROM
                (SELECT pd.dataproperty, pd.datatype, p.changed AS o_date, p.*
                  FROM property p
                  LEFT JOIN property_definition pd ON pd.keyname = p.property_definition_keyname
                 WHERE p.changed >= '%(first_second)s' and p.created <= '%(last_second)s'
                 ORDER BY o_date
                ) ch
                UNION SELECT * FROM
                (SELECT pd.dataproperty, pd.datatype, p.deleted AS o_date, p.*
                  FROM property p
                  LEFT JOIN property_definition pd ON pd.keyname = p.property_definition_keyname
                 WHERE p.deleted >= '%(first_second)s' and p.created <= '%(last_second)s'
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
                 WHERE p.created > '%(date)s'
                 ORDER BY o_date
                 LIMIT %(limit)s
                ) cr
                UNION SELECT * FROM
                (SELECT pd.dataproperty, pd.datatype, p.changed AS o_date, p.*
                  FROM property p
                  LEFT JOIN property_definition pd ON pd.keyname = p.property_definition_keyname
                 WHERE p.changed > '%(date)s'
                 ORDER BY o_date
                 LIMIT %(limit)s
                ) ch
                UNION SELECT * FROM
                (SELECT pd.dataproperty, pd.datatype, p.deleted AS o_date, p.*
                  FROM property p
                  LEFT JOIN property_definition pd ON pd.keyname = p.property_definition_keyname
                 WHERE p.deleted > '%(date)s'
                 ORDER BY o_date
                 LIMIT %(limit)s
                ) de
                ORDER BY o_date
                 LIMIT %(limit)s
                """ % {'limit': lim, 'date': first_second}


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


    def check_formula(self, property_row, direction):
        sql = {}
        # Parent formula properties with ".child." in its value_formula (SLQ is NOT tested)
        sql['parent'] = """
            SELECT p_formula.*
            FROM relationship r
            LEFT JOIN entity e_formula ON e_formula.id = r.entity_id
                      AND e_formula.is_deleted = 0
            LEFT JOIN property p_formula ON p_formula.entity_id = e_formula.id
                      AND p_formula.is_deleted = 0
            RIGHT JOIN property_definition pd ON p_formula.property_definition_keyname = pd.keyname
                      AND pd.formula = 1
                      AND p_formula.value_formula LIKE concat('%%%%.child.',pd.entity_definition_keyname,'.%s}%%%%')
            WHERE r.related_entity_id = %s
              AND r.relationship_definition_keyname = 'child'
              AND r.is_deleted = 0
              AND ifnull(p_formula.changed, "%s") < "%s";
        """ % (property_row.dataproperty, property_row.entity_id, datetime.min, property_row.created)

        # Child formula properties (SLQ is NOT tested)
        sql['child'] = """
            SELECT p_formula.*
            FROM relationship r
            LEFT JOIN entity e_formula ON e_formula.id = r.related_entity_id
                      AND e_formula.is_deleted = 0
            LEFT JOIN property p_formula ON p_formula.entity_id = e_formula.id
                      AND p_formula.is_deleted = 0
            RIGHT JOIN property_definition pd ON p_formula.property_definition_keyname = pd.keyname
                      AND pd.formula = 1
                      AND p_formula.value_formula LIKE concat('%%%%.-child.',pd.entity_definition_keyname,'.%s}%%%%')
            WHERE r.entity_id = %s
              AND r.relationship_definition_keyname = 'child'
              AND r.is_deleted = 0
              AND ifnull(p_formula.changed, "%s") < "%s";
        """ % (property_row.dataproperty, property_row.entity_id, datetime.min, property_row.created)

        # Self referencing formula properties (SLQ is NOT tested)
        sql['self'] = """
            SELECT p_formula.id, p_formula.entity_id, p_formula.value_formula, p_formula.value_string
            FROM entity e_formula
            LEFT JOIN property p_formula ON p_formula.entity_id = e_formula.id
                        AND p_formula.is_deleted = 0
                        AND p_formula.value_formula LIKE concat('%%%%{self.%s}%%%%')
            RIGHT JOIN property_definition pd ON pd.keyname = p_formula.property_definition_keyname
                        AND pd.formula = 1
            WHERE e_formula.is_deleted = 0
              AND e_formula.id = %s
              AND ifnull(p_formula.changed, "%s") < "%s";
        """ % (property_row.dataproperty, property_row.entity_id, datetime.min, property_row.created)

        # Back-referencing formula properties (SLQ is tested)
        sql['back-referencing'] = """
            SELECT p_formula.id, p_formula.entity_id, p_formula.value_formula, p_formula.value_string
            FROM property p_reference
            RIGHT JOIN property_definition pd_reference ON pd_reference.keyname = p_reference.property_definition_keyname
                        AND pd_reference.datatype = 'reference'
            LEFT JOIN entity e_formula ON e_formula.id = p_reference.value_reference
                        AND e_formula.is_deleted = 0
            LEFT JOIN property p_formula ON p_formula.entity_id = e_formula.id
                        AND p_formula.is_deleted = 0
                        AND p_formula.value_formula LIKE concat('%%%%.-', pd_reference.dataproperty, '.%%%%')
            RIGHT JOIN property_definition pd2 ON pd2.keyname = p_formula.property_definition_keyname
                        AND pd2.formula = 1
            WHERE p_reference.is_deleted = 0
              AND p_reference.entity_id = %s
              AND ifnull(p_formula.changed, "%s") < "%s";
        """ % (property_row.entity_id, datetime.min, property_row.created)

        return sql[direction]


    def searchindex(self, entity_id):
        return """
            INSERT INTO searchindex (entity_id, `language`, val)
             SELECT
                p.entity_id,
                l.language,
                @val := LEFT(GROUP_CONCAT(p.value_string ORDER BY pd.ordinal, p.id SEPARATOR ' '), 2000)
            FROM (SELECT DISTINCT t.language FROM translation t WHERE t.language IS NOT NULL) AS l
            LEFT JOIN  property AS p ON ifnull(p.language,l.language) = l.language
            LEFT JOIN  property_definition AS pd ON pd.keyname = p.property_definition_keyname
            WHERE p.entity_id = %i
            AND p.is_deleted = 0
            AND pd.is_deleted = 0
            AND pd.search = 1
            GROUP BY
                l.language,
                p.entity_id
            ON DUPLICATE KEY UPDATE
                val = @val;
        """ % (entity_id)



def formatDatetime(date, format='%(day)02d.%(month)02d.%(year)d %(hour)02d:%(minute)02d'):
    """
    Formats and returns date as string. Format tags are %(day)02d, %(month)02d, %(year)d, %(hour)02d and %(minute)02d.

    """
    if not date:
        return ''
    return format % {'year': date.year, 'month': date.month, 'day': date.day, 'hour': date.hour, 'minute': date.minute}


