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

db = torndb.Connection(
    host     = args.database_host,
    database = args.database_name,
    user     = args.database_user,
    password = args.database_password,
)

sql = """
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
                ) AS VALUE
FROM entity mge
LEFT JOIN property mgp ON mgp.entity_id = mge.id AND mgp.is_deleted = 0 AND mgp.property_definition_keyname = 'maintenancegroup-name'
LEFT JOIN property rp ON rp.value_reference = mge.id AND rp.is_deleted = 0
LEFT JOIN property cp ON cp.entity_id = rp.entity_id AND cp.is_deleted = 0
LEFT JOIN property_definition cpd ON cpd.keyname = cp.property_definition_keyname AND cpd.is_deleted = 0
WHERE mge.is_deleted = 0
AND mge.entity_definition_keyname = 'maintenancegroup'
ORDER BY cp.entity_id, cpd.ordinal;
"""

customers = {}
for c in db.query(sql):
    customers.setdefault(c.maintenancegroup_id, {})['name'] = c.maintenancegroup_name
    customers[c.maintenancegroup_id]['customers'].setdefault(c.entity, {})[c.property] = c.value

print customers