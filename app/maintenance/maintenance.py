# maintenance.py
from datetime import datetime
import os, sys
import argparse
import json
import time

from taskdb import *

parser = argparse.ArgumentParser()
parser.add_argument('--database-host',     required = True)
parser.add_argument('--database-name',     required = True)
parser.add_argument('--database-user',     required = True)
parser.add_argument('--database-password', required = True)
parser.add_argument('--customergroup',  required = False, default = '0')
args = parser.parse_args()

# print args

cg_db = torndb.Connection(
    host     = args.database_host,
    database = args.database_name,
    user     = args.database_user,
    password = args.database_password,
)

# Customer groups and customers in groups are reloaded on every iteration
cg_sql = """
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
""" % (args.customergroup, args.customergroup)

print cg_sql


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
maintenance_sql = filespace_optimized_sql

while True:
    customers = {}
    processed_customers = []

    for c in cg_db.query(cg_sql):
        customers.setdefault(c.entity, {})[c.property] = c.value

    # print json.dumps(customers, sort_keys=True, indent=4, separators=(',', ': '))

    for customer_row in customers.values():
        # print json.dumps(customers, sort_keys=True, indent=4, separators=(',', ': '))
        if customer_row.get('database-name') not in known_customers:
            print "New customer added to roundtrip: %s." % (customer_row.get('database-name'))

        db = torndb.Connection(
            host     = customer_row.get('database-host'),
            database = customer_row.get('database-name'),
            user     = customer_row.get('database-user'),
            password = customer_row.get('database-password'),
        )
        db.execute(maintenance_sql)

        processed_customers.append(customer_row.get('database-name'))

    known_customers = processed_customers
    maintenance_sql = speed_optimized_sql

    time.sleep(1)
    # print json.dumps(customers, sort_keys=True, indent=4, separators=(',', ': '))















