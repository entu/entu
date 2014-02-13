# maintenance.py
from datetime import datetime
import os, sys
import argparse
import json
import time

from taskdb import *

# lib_path = os.path.abspath('../main')
# sys.path.append(lib_path)
# from helper import myDatabase

parser = argparse.ArgumentParser()
parser.add_argument('--database-host',     required = True)
parser.add_argument('--database-name',     required = True)
parser.add_argument('--database-user',     required = True)
parser.add_argument('--database-password', required = True)
args = parser.parse_args()

# print args

mg_db = torndb.Connection(
    host     = args.database_host,
    database = args.database_name,
    user     = args.database_user,
    password = args.database_password,
)

# Maintenance groups and customers in groups are reloaded on every iteration
mg_sql = """
SELECT DISTINCT mge.id AS maintenancegroup_id, mgp.value_string AS maintenancegroup_name,
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
FROM entity mge
LEFT JOIN property mgp ON mgp.entity_id = mge.id AND mgp.is_deleted = 0 AND mgp.property_definition_keyname = 'maintenancegroup-name'
LEFT JOIN property rp ON rp.value_reference = mge.id AND rp.is_deleted = 0
LEFT JOIN property cp ON cp.entity_id = rp.entity_id AND cp.is_deleted = 0
LEFT JOIN property_definition cpd ON cpd.keyname = cp.property_definition_keyname
WHERE mge.is_deleted = 0
AND cpd.is_deleted = 0
AND mge.entity_definition_keyname = 'maintenancegroup'
ORDER BY cp.entity_id, cpd.ordinal;
"""

# SQL for every maintenance group is also reloaded on each roundtrip
mg_sql_sql = """
SELECT mge.id, sqp.value_text
FROM entity mge
LEFT JOIN property mgp ON mgp.entity_id = mge.id AND mgp.is_deleted = 0 AND mgp.property_definition_keyname = 'maintenancegroup-sql'
LEFT JOIN property sqp ON sqp.entity_id = mgp.value_reference AND sqp.is_deleted = 0 AND sqp.property_definition_keyname = 'sql-sequel'
WHERE mge.entity_definition_keyname = 'maintenancegroup';
"""


# First run is with slower query that takes less temporary filespace
filespace_optimized_sql = """
INSERT INTO searchindex (entity_id, language, val, last_property_id) SELECT
    p.entity_id,
    ifnull(p.language,''),
    @val := LEFT(GROUP_CONCAT(p.value_string ORDER BY pd.ordinal, p.id SEPARATOR ' '), 2000),
    @max_id := MAX(p.id)
FROM
    entity AS e,
    property AS p,
    property_definition AS pd
WHERE p.entity_id = e.id
AND pd.keyname = p.property_definition_keyname
AND e.is_deleted  = 0
AND p.is_deleted = 0
AND pd.is_deleted = 0
AND pd.search = 1
AND e.id IN (
    SELECT entity_id
    FROM property, property_definition
    WHERE property_definition.keyname = property.property_definition_keyname
    AND property.is_deleted = 0
    AND property_definition.is_deleted = 0
    AND property_definition.search = 1
    AND property.id > (SELECT IFNULL(MAX(last_property_id), 0) FROM searchindex)
)
GROUP BY
    p.language,
    p.entity_id
ON DUPLICATE KEY UPDATE
    val = @val,
    last_property_id = @max_id;
"""

# Next runs are incremental and optimized for speed rather than temporary disk usage.
speed_optimized_sql = """
INSERT INTO searchindex (entity_id, LANGUAGE, val, last_property_id)
SELECT p.entity_id,
     ifnull(p.language,''),
     @val := LEFT(GROUP_CONCAT(ixp.value_string ORDER BY ixpd.ordinal, ixp.id SEPARATOR ' '), 2000),
     @max_id := MAX(ixp.id)
FROM property p
RIGHT JOIN property_definition pd ON pd.keyname = p.property_definition_keyname AND pd.search = 1 AND pd.is_deleted = 0
LEFT JOIN property ixp ON ixp.entity_id = p.entity_id AND ixp.is_deleted = 0
RIGHT JOIN property_definition ixpd ON ixpd.keyname = ixp.property_definition_keyname AND ixpd.search = 1 AND ixpd.is_deleted = 0
WHERE p.id > (SELECT IFNULL(MAX(last_property_id), 0) FROM searchindex)
AND p.is_deleted = 0
    GROUP BY
        ixp.language,
        ixp.entity_id
    ON DUPLICATE KEY UPDATE
        val = @val,
        last_property_id = @max_id;
"""


known_customers = []

while True:
    customers = {}
    processed_customers = []

    for c in mg_db.query(mg_sql):
        customers.setdefault(c.maintenancegroup_id, {})['name'] = c.maintenancegroup_name
        customers[c.maintenancegroup_id].setdefault('customers', {}).setdefault(c.entity, {})[c.property] = c.value
    for s in mg_db.query(mg_sql_sql):
        customers[s.id].setdefault('sql', []).append(s.value_text)

    # print json.dumps(customers, sort_keys=True, indent=4, separators=(',', ': '))


    for maintgroup_row in customers.values():
        for customer_row in maintgroup_row['customers'].values():
            # print json.dumps(customers, sort_keys=True, indent=4, separators=(',', ': '))
            if customer_row.get('database-name') not in known_customers:
                print "New customer added to roundtrip: %s." % (customer_row.get('database-name'))

            db = torndb.Connection(
                host     = customer_row.get('database-host'),
                database = customer_row.get('database-name'),
                user     = customer_row.get('database-user'),
                password = customer_row.get('database-password'),
            )
            for sql_row in maintgroup_row['sql']:
                # print sql_row
                db.execute(sql_row)

            processed_customers.append(customer_row.get('database-name'))

    known_customers = processed_customers

    time.sleep(1)
    # print json.dumps(customers, sort_keys=True, indent=4, separators=(',', ': '))















