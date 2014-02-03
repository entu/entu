# taskqueue.py
from datetime import datetime
import os, sys
import argparse

from taskdb import *

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

print args

timestamp_file = 'taskqueue.time'
last_checked = datetime.min
now = datetime.now()
try:
    with open(timestamp_file, 'r+') as f:
        last_checked = f.read()
except IOError as e:
    # print "I/O error({0}): {1}: {2}".format(e.errno, e.strerror, timestamp_file)
    print "No timestamp file {0} - defaulting to {1}".format(timestamp_file, last_checked)


db = myDatabase()

databases = db.get_app_settings(args)
for cust in databases.values():
    print "\n================= {0}".format(datetime.now())
    print "== {0} ==".format(cust.get('domain'))
    db = torndb.Connection(
        host     = cust.get('database-host'),
        database = cust.get('database-name'),
        user     = cust.get('database-user'),
        password = cust.get('database-password'),
    )

    sql = """
        SELECT *
        FROM property p
        WHERE is_deleted = 0
          AND created =
            (SELECT created
             FROM property
             WHERE is_deleted = 0
               AND created > "0001-01-01 00:00:00"
             ORDER BY created LIMIT 1);
    """

    for row in db.query(sql):
        print row

    db.close()


