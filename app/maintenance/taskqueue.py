# taskqueue.py
from datetime import datetime
import os, sys
import argparse
import json
import time

from taskdb import *
from formula import *

# lib_path = os.path.abspath('../main')
# sys.path.append(lib_path)
# from helper import myDatabase

parser = argparse.ArgumentParser()
parser.add_argument('--database-host', required=True)
parser.add_argument('--database-name', required=True)
parser.add_argument('--database-user', required=True)
parser.add_argument('--database-password', required=True)
parser.add_argument('--customer-group', required=True)
args = parser.parse_args()

# print args



def revaluate_formulas(recordset):
    rows_updated = 0
    rows_up_to_date = 0
    # print "----"
    # raw_input("Starting revaluation for {0} rows. Press a key...".format(len(recordset)))
    for formula_property_row in recordset:
        frm = Formula(db, formula_property_row.id, formula_property_row.entity_id, formula_property_row.value_formula)
        frm_value = ', '.join(frm.evaluate())
        # print "Old value is: %s" % (formula_property_row.value_string)
        # print "Formula evaluated to: %s" % (frm_value)
        if frm_value != formula_property_row.value_string:
            print formula_property_row
            rows_updated = rows_updated + 1
            print "'%s' != '%s'. Updating" % (frm_value, formula_property_row.value_string)
            sql = """
                UPDATE property
                SET value_string = "%s", changed = now(), changed_by = 'taskqueue' WHERE id = %s
            """ % (frm_value, formula_property_row.id)
            db.execute(sql)
        else:
            rows_up_to_date = rows_up_to_date + 1
            # print "%s equals %s, updating changed and changed_by values" % (frm_value, formula_property_row.value_string)
            sql = """
                UPDATE property
                SET changed = now(), changed_by = 'taskqueue' WHERE id = %s
            """ % formula_property_row.id
            db.execute(sql)

    if rows_updated > 0:
        # raw_input('Revaluation of {0} rows finished.\n=> {1} rows updated\n=> {2} rows were up to date.\nPress a key...'.format(len(recordset), rows_updated, rows_up_to_date))
        print 'Revaluation of {0} rows finished.\n=> {1} rows updated\n=> {2} rows were up to date.'.format(len(recordset), rows_updated, rows_up_to_date)



timestamp_file = 'taskqueue.time'
# last_checked = datetime.min
last_checked = {}
try:
    with open(timestamp_file, 'r+') as f:
        last_checked = json.loads(f.read())
except IOError as e:
    # print "I/O error({0}): {1}: {2}".format(e.errno, e.strerror, timestamp_file)
    print "No timestamp file {0}.".format(timestamp_file)

mov_ave = 0.99
chunk_size = 100

customer_db = myDatabase()


while True:
    databases = customer_db.get_app_settings(args)
    customer_count = len(databases)

    for customer_row in databases.values():
        db = torndb.Connection(
            host     = customer_row.get('database-host'),
            database = customer_row.get('database-name'),
            user     = customer_row.get('database-user'),
            password = customer_row.get('database-password'),
        )

        # print customer_row.get('domain')

        last_checked.setdefault(customer_row.get('domain'), 0)
        last_checked.setdefault('_tq:metrics', {'properties_checked': 0.0000, 'time_spent': 0.0000})

        customer_started_at = datetime.now()

        sql = """
            SELECT pd.dataproperty, p.*
            FROM property p
            LEFT JOIN property_definition pd ON pd.keyname = p.property_definition_keyname
            WHERE p.id > %s
            ORDER BY p.id
            LIMIT %s
            ;
        """ % (last_checked[customer_row.get('domain')], chunk_size)
        # print sql

        properties_to_check = len(db.query(sql))
        if properties_to_check == 0:
            # print "Nothing to do. Sleeping some and looking for next customer."
            # time.sleep(0.1)
            continue

        sys.stdout.write("== %s: %25s. Checking %3i properties... " % (datetime.now(), customer_row.get('domain'), properties_to_check))
        sys.stdout.flush()

        for property_row in db.query(sql):
            # print property_row

            # Parent formula properties with ".child." in its value_formula (SLQ is NOT tested)
            sql = """
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
            # print sql
            if len(db.query(sql)) > 0:
                # print "Have {0} matching parent formulas.".format(len(db.query(sql)))
                # print property_row
                revaluate_formulas(db.query(sql))

            # Child formula properties (SLQ is NOT tested)
            sql = """
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
            if len(db.query(sql)) > 0:
                # print sql
                # print "Have {0} matching child formulas.".format(len(db.query(sql)))
                # print property_row
                revaluate_formulas(db.query(sql))

            # Back-referencing formula properties (SLQ is tested)
            sql = """
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
            # print sql
            if len(db.query(sql)) > 0:
                # print "Have {0} matching back-referencing formulas.".format(len(db.query(sql)))
                # print property_row
                revaluate_formulas(db.query(sql))

            last_checked[customer_row.get('domain')] = property_row.id

        db.close()


        customer_finished_at = datetime.now()
        customer_time_spent = customer_finished_at - customer_started_at

        last_checked['_tq:metrics']['properties_checked'] = mov_ave * last_checked['_tq:metrics']['properties_checked'] + properties_to_check
        last_checked['_tq:metrics']['time_spent'] = mov_ave * last_checked['_tq:metrics']['time_spent'] + customer_time_spent.microseconds + (customer_time_spent.seconds + customer_time_spent.days * 86400) * 1000000
        # print last_checked
        print "Moving average (%1.2f) properties/second: %3.2f." % (mov_ave, 1000000.00*last_checked['_tq:metrics']['properties_checked']/last_checked['_tq:metrics']['time_spent'])
        with open(timestamp_file, 'w+') as f:
            f.write(json.dumps(last_checked, sort_keys=True, indent=4, separators=(',', ': ')))

    # time.sleep(0.02)
    # raw_input('Enter your input:')

