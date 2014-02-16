# maintenance.py
from datetime import datetime
import os, sys
import argparse
import json
import time

from etask import *


parser = argparse.ArgumentParser()
parser.add_argument('--database-host',     required = True)
parser.add_argument('--database-name',     required = True)
parser.add_argument('--database-user',     required = True)
parser.add_argument('--database-password', required = True)
parser.add_argument('--customergroup',  required = False, default = '0')
args = parser.parse_args()

# print args

task = ETask(args)

known_customers = []
i = 1
sleep = 1.12

while True:
    d_start = datetime.now()
    sys.stdout.write("Run no. %s. %22s ." % (i, d_start))
    sys.stdout.flush()
    processed_customers = []

    # print json.dumps(task.customers, sort_keys=True, indent=4, separators=(',', ': '))

    for customer_row in task.customers.values():
        # print json.dumps(customers, sort_keys=True, indent=4, separators=(',', ': '))
        db = torndb.Connection(
            host     = customer_row.get('database-host'),
            database = customer_row.get('database-name'),
            user     = customer_row.get('database-user'),
            password = customer_row.get('database-password'),
        )
        if customer_row.get('database-name') not in known_customers:
            # print "%s: New customer added to roundtrip: %s." % (datetime.now(), customer_row.get('database-name'))
            try:
                db.execute(EQuery().searchindex('slow'))
            except:
                print EQuery().searchindex('slow')
                print "\n%s: failed for %s." % (datetime.now(), customer_row.get('database-name'))
        else:
            try:
                db.execute(EQuery().searchindex('fast'))
            except:
                print EQuery().searchindex('fast')
                print "\n%s: failed for %s." % (datetime.now(), customer_row.get('database-name'))

        processed_customers.append(customer_row.get('database-name'))

    known_customers = processed_customers

    d_stop = datetime.now()
    time_delta = d_stop - d_start
    time_spent_sec = 1.0*time_delta.microseconds/1000000 + time_delta.seconds + time_delta.days*86400
    sleep = time_spent_sec / 5
    print ".. %22s (%2.2f seconds). Now sleeping for %2.2f seconds." % (d_stop, time_spent_sec, sleep)
    time.sleep(sleep)
    i += 1
    # print json.dumps(customers, sort_keys=True, indent=4, separators=(',', ': '))















