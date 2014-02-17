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



timestamp_file = 'taskqueue.time'
last_checked = {}
try:
    with open(timestamp_file, 'r+') as f:
        last_checked = json.loads(f.read())
except IOError as e:
    print "No timestamp file {0}.".format(timestamp_file)

task = ETask(args)

known_customers = []
i = 1
sleepfactor = 0.05
mov_ave = 0.99
chunk_size = 2500


while True:
    d_start = datetime.now()
    sys.stdout.write("Run no. %s. %22s ." % (i, d_start))
    sys.stdout.flush()
    processed_customers = []

    task.reload_customers()
    # print json.dumps(task.customers, sort_keys=True, indent=4, separators=(',', ': '))

    for customer_row in task.customers.values():
        # print json.dumps(customers, sort_keys=True, indent=4, separators=(',', ': '))
        db = torndb.Connection(
            host     = customer_row.get('database-host'),
            database = customer_row.get('database-name'),
            user     = customer_row.get('database-user'),
            password = customer_row.get('database-password'),
        )

        last_checked.setdefault(customer_row.get('domain'), {}).setdefault('last_id', 0)
        last_checked.setdefault(customer_row.get('domain'), {}).setdefault('latest_checked', '1001-01-01 00:00:00')
        last_checked.setdefault('_tq:metrics', {'properties_checked': 0.0000, 'time_spent': 0.0000})
        # print last_checked

        customer_started_at = datetime.now()

        property_table = db.query(EQuery().fresh_properties(chunk_size, last_checked[customer_row.get('domain')]['latest_checked']))
        properties_to_check = len(property_table)
        if properties_to_check == 0:
            continue
        sys.stdout.write(".. Checking %i properties for %s ." % (properties_to_check, customer_row.get('domain')))
        sys.stdout.flush()

        for property_row in property_table:
            task.check_my_formulas(db, property_row)

            last_checked[customer_row.get('domain')]['last_id'] = property_row.id
            last_checked[customer_row.get('domain')]['latest_checked'] = str(property_row.o_date)



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



        customer_finished_at = datetime.now()
        customer_time_spent = customer_finished_at - customer_started_at

        last_checked['_tq:metrics']['properties_checked'] = mov_ave * last_checked['_tq:metrics']['properties_checked'] + properties_to_check
        last_checked['_tq:metrics']['time_spent'] = mov_ave * last_checked['_tq:metrics']['time_spent'] + customer_time_spent.microseconds + (customer_time_spent.seconds + customer_time_spent.days * 86400) * 1000000

        with open(timestamp_file, 'w+') as f:
            f.write(json.dumps(last_checked, sort_keys=True, indent=4, separators=(',', ': ')))



    known_customers = processed_customers

    d_stop = datetime.now()
    time_delta = d_stop - d_start
    time_spent_sec = 0.000001*time_delta.microseconds + time_delta.seconds + time_delta.days*86400
    sleep = time_spent_sec * sleepfactor + sleepfactor
    print ".. %22s (%2.2f seconds). Now sleeping for %2.2f seconds." % (d_stop, time_spent_sec, sleep)
    print "Moving average (%1.2f) properties/second: %3.2f." % (mov_ave, 1000000.00*last_checked['_tq:metrics']['properties_checked']/last_checked['_tq:metrics']['time_spent'])
    time.sleep(sleep)
    i += 1
    # print json.dumps(customers, sort_keys=True, indent=4, separators=(',', ': '))















