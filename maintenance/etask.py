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

        qresult = db.query(EQuery().check_formula(property_row, 'back-referencing'))
        if len(qresult) > 0:
            # print "Have {0} matching back-referencing formulas.".format(len(qresult))
            # print property_row
            self.revaluate_formulas(db, qresult)


    def revaluate_formulas(self, db, recordset):
        rows_updated = 0
        rows_up_to_date = 0
        # print "----"
        # raw_input("Starting revaluation for {0} rows. Press a key...".format(len(recordset)))

        for formula_property_row in recordset:
            frm = Formula(db, formula_property_row.id, formula_property_row.entity_id, formula_property_row.value_formula)
            frm_value = ''.join(frm.evaluate())
            print "Old value is: %s" % (formula_property_row.value_string)
            print "Formula evaluated to: %s" % (frm_value)
            if frm_value != formula_property_row.value_string:
                print formula_property_row
                rows_updated = rows_updated + 1
                print "'%s' != '%s'. Updating..." % (frm_value, formula_property_row.value_string)

                sql = """
                INSERT INTO `property` (`property_definition_keyname`, `entity_id`, `ordinal`, `language`, `value_formula`, `value_string`, `value_text`, `value_integer`, `value_decimal`, `value_boolean`, `value_datetime`, `value_entity`, `value_reference`, `value_file`, `value_counter`, `created`, `created_by`, `changed`, `changed_by`)
                SELECT `property_definition_keyname`, `entity_id`, `ordinal`, `language`, `value_formula`, '%s', `value_text`, `value_integer`, `value_decimal`, `value_boolean`, `value_datetime`, `value_entity`, `value_reference`, `value_file`, `value_counter`, `created`, `created_by`, now(), 'maintenance'
                FROM `property` WHERE id = %s;
                """ % (frm_value, formula_property_row.id)
                db.execute(sql)

                sql = """
                    UPDATE property
                    SET deleted = now(), deleted_by = 'maintenance', is_deleted = 1 WHERE id = %s
                """ % (formula_property_row.id)
                db.execute(sql)
                continue
            else:
                rows_up_to_date = rows_up_to_date + 1
                print "%s equals %s, updating changed and changed_by values" % (frm_value, formula_property_row.value_string)
                sql = """
                    UPDATE property
                    SET changed = now(), changed_by = 'maintenance' WHERE id = %s
                """ % formula_property_row.id
                db.execute(sql)

        if rows_updated > 0:
            # raw_input('Revaluation of {0} rows finished.\n=> {1} rows updated\n=> {2} rows were up to date.\nPress a key...'.format(len(recordset), rows_updated, rows_up_to_date))
            print 'Revaluation of {0} rows finished.\n=> {1} rows updated\n=> {2} rows were up to date.'.format(len(recordset), rows_updated, rows_up_to_date)





class EQuery():


    def fresh_properties(self, lim, date, dense = False):
        #   These queries should be rewritten to retrieve specific columns only not select *
        # and grouped for max(o_date)
        if dense:
            return """
                SELECT *
                FROM
                (SELECT pd.dataproperty, p.created AS o_date, p.*
                  FROM property p
                  LEFT JOIN property_definition pd ON pd.keyname = p.property_definition_keyname
                 WHERE p.created = '%(date)s'
                 ORDER BY o_date
                ) cr
                UNION SELECT * FROM
                (SELECT pd.dataproperty, p.changed AS o_date, p.*
                  FROM property p
                  LEFT JOIN property_definition pd ON pd.keyname = p.property_definition_keyname
                 WHERE p.changed = '%(date)s'
                 ORDER BY o_date
                ) ch
                UNION SELECT * FROM
                (SELECT pd.dataproperty, p.deleted AS o_date, p.*
                  FROM property p
                  LEFT JOIN property_definition pd ON pd.keyname = p.property_definition_keyname
                 WHERE p.deleted = '%(date)s'
                 ORDER BY o_date
                ) de
                ORDER BY o_date
                """ % {'date': date}
        else:
            return """
                SELECT *
                FROM
                (SELECT pd.dataproperty, p.created AS o_date, p.*
                  FROM property p
                  LEFT JOIN property_definition pd ON pd.keyname = p.property_definition_keyname
                 WHERE p.created > '%(date)s'
                 ORDER BY o_date
                 LIMIT %(limit)s
                ) cr
                UNION SELECT * FROM
                (SELECT pd.dataproperty, p.changed AS o_date, p.*
                  FROM property p
                  LEFT JOIN property_definition pd ON pd.keyname = p.property_definition_keyname
                 WHERE p.changed > '%(date)s'
                 ORDER BY o_date
                 LIMIT %(limit)s
                ) ch
                UNION SELECT * FROM
                (SELECT pd.dataproperty, p.deleted AS o_date, p.*
                  FROM property p
                  LEFT JOIN property_definition pd ON pd.keyname = p.property_definition_keyname
                 WHERE p.deleted > '%(date)s'
                 ORDER BY o_date
                 LIMIT %(limit)s
                ) de
                ORDER BY o_date
                 LIMIT %(limit)s
                """ % {'limit': lim, 'date': date}


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


    def searchindex(self, entity_id = None):
        if not entity_id:
            return """
                INSERT INTO searchindex (entity_id, `language`, val)
                 SELECT
                    p.entity_id,
                    ifnull(p.language,''),
                    @val := LEFT(GROUP_CONCAT(p.value_string ORDER BY pd.ordinal, p.id SEPARATOR ' '), 2000)
                FROM
                    property AS p
                    LEFT JOIN  property_definition AS pd ON pd.keyname = p.property_definition_keyname
                WHERE p.is_deleted = 0
                AND pd.is_deleted = 0
                AND pd.search = 1
                GROUP BY
                    p.language,
                    p.entity_id
                ON DUPLICATE KEY UPDATE
                    val = @val;
            """

        if entity_id:
            return """
                INSERT INTO searchindex (entity_id, `language`, val)
                 SELECT
                    p.entity_id,
                    ifnull(p.language,''),
                    @val := LEFT(GROUP_CONCAT(p.value_string ORDER BY pd.ordinal, p.id SEPARATOR ' '), 2000)
                FROM
                    property AS p
                    LEFT JOIN  property_definition AS pd ON pd.keyname = p.property_definition_keyname
                WHERE p.entity_id = %i
                AND p.is_deleted = 0
                AND pd.is_deleted = 0
                AND pd.search = 1
                GROUP BY
                    p.language,
                    p.entity_id
                ON DUPLICATE KEY UPDATE
                    val = @val;
            """ % (entity_id)


    # Obsolete
    # def searchindex(self, speed):
    #     sql = {}
    #     # First run is with slower query that takes less temporary filespace
    #     sql['slow'] = """
    #         INSERT INTO searchindex (entity_id, language, val, last_property_id) SELECT
    #             p.entity_id,
    #             ifnull(p.language,''),
    #             @val := LEFT(GROUP_CONCAT(p.value_string ORDER BY pd.ordinal, p.id SEPARATOR ' '), 2000),
    #             @max_id := MAX(p.id)
    #         FROM
    #             entity AS e,
    #             property AS p,
    #             property_definition AS pd
    #         WHERE p.entity_id = e.id
    #         AND pd.keyname = p.property_definition_keyname
    #         AND e.is_deleted  = 0
    #         AND p.is_deleted = 0
    #         AND pd.is_deleted = 0
    #         AND pd.search = 1
    #         AND e.id IN (
    #             SELECT entity_id
    #             FROM property, property_definition
    #             WHERE property_definition.keyname = property.property_definition_keyname
    #             AND property.is_deleted = 0
    #             AND property_definition.is_deleted = 0
    #             AND property_definition.search = 1
    #             AND property.id > (SELECT IFNULL(MAX(last_property_id), 0) FROM searchindex)
    #         )
    #         GROUP BY
    #             p.language,
    #             p.entity_id
    #         ON DUPLICATE KEY UPDATE
    #             val = @val,
    #             last_property_id = @max_id;
    #         """
    #     # Next runs are incremental and optimized for speed rather than temporary disk usage.
    #     sql['fast'] = """
    #         INSERT INTO searchindex (entity_id, LANGUAGE, val, last_property_id)
    #         SELECT p.entity_id,
    #              ifnull(p.language,''),
    #              @val := LEFT(GROUP_CONCAT(ixp.value_string ORDER BY ixpd.ordinal, ixp.id SEPARATOR ' '), 2000),
    #              @max_id := MAX(ixp.id)
    #         FROM property p
    #         RIGHT JOIN property_definition pd ON pd.keyname = p.property_definition_keyname AND pd.search = 1 AND pd.is_deleted = 0
    #         LEFT JOIN property ixp ON ixp.entity_id = p.entity_id AND ixp.is_deleted = 0
    #         RIGHT JOIN property_definition ixpd ON ixpd.keyname = ixp.property_definition_keyname AND ixpd.search = 1 AND ixpd.is_deleted = 0
    #         WHERE p.id > (SELECT IFNULL(MAX(last_property_id), 0) FROM searchindex)
    #         AND p.is_deleted = 0
    #             GROUP BY
    #                 ixp.language,
    #                 ixp.entity_id
    #             ON DUPLICATE KEY UPDATE
    #                 val = @val,
    #                 last_property_id = @max_id;
    #         """
    #     return sql[speed]

