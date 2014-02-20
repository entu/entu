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
parser.add_argument('-v', '--verbose',  action = 'count')
args = parser.parse_args()

# Set verbosity level
verbose = 0
if args.verbose:
    verbose = args.verbose

timestamp_file = 'taskqueue.time'
last_checked = {}
try:
    with open(timestamp_file, 'r+') as f:
        last_checked = json.loads(f.read())
except IOError as e:
    print "No timestamp file {0}.".format(timestamp_file)

task = ETask(args)

i = 0
known_customers = {}
processed_customers = {}
sleepfactor = 0.05
mov_ave = 0.99
chunk_size = 2500


while True:
    d_start = datetime.now()
    i = last_checked.setdefault('_tq:metrics', {}).setdefault('run_id', 0)
    sys.stdout.write("-- Run no. %s. %22s.\n" % (i, d_start))
    sys.stdout.flush()


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
        last_checked.setdefault('_tq:metrics', {}).setdefault('properties_checked', 0.0000)
        last_checked.setdefault('_tq:metrics', {}).setdefault('time_spent', 0.0000)



        customer_started_at = datetime.now()
        if verbose > 1: print "%s Starting for --== %s ==--." % (datetime.now()-d_start, customer_row.get('domain'))

        check_time = last_checked[customer_row.get('domain')]['latest_checked']
        if verbose > 1: print "%s Looking for properties fresher than %s." % (datetime.now()-d_start, check_time)
        property_table = db.query(EQuery().fresh_properties(chunk_size, check_time, False))
        properties_to_check = len(property_table)
        if verbose > 1: print "%s Got %s properties." % (datetime.now()-d_start, properties_to_check)
        # If chunk size of rows returned, then reload query with next second properties only.
        if properties_to_check == chunk_size:
            single_second = property_table[0].o_date
            if verbose > 1: print "%s Reloading properties with timestamp %s." % (datetime.now()-d_start, single_second)
            try:
                property_table = db.query(EQuery().fresh_properties(chunk_size, single_second, True))
            except:
                print EQuery().fresh_properties(chunk_size, single_second, True)
                print "\n%s: failed for %s." % (datetime.now(), customer_row.get('database-name'))

            properties_to_check = len(property_table)
            if verbose > 1: print "%s Got %s properties with timestamp of %s." % (datetime.now()-d_start, properties_to_check, single_second)
        if properties_to_check == 0:
            continue


        if verbose > 1: print "%s Checking formulas of %i properties." % (datetime.now()-d_start, properties_to_check)

        for property_row in property_table:
            task.check_my_formulas(db, property_row)

            last_checked[customer_row.get('domain')]['last_id'] = property_row.id
            last_checked[customer_row.get('domain')]['latest_checked'] = str(property_row.o_date)

        if verbose > 1: print "%s Formula check finished." % (datetime.now()-d_start)


        if customer_row.get('database-name') not in known_customers.values():
            if verbose > 0: print "%s New customer added to roundtrip: %s. Indexing all entities." % (datetime.now()-d_start, customer_row.get('database-name'))

            try:
                if verbose > 0: print EQuery().searchindex()
                db.execute(EQuery().searchindex())
            except:
                if verbose > 0: print "%s: failed for %s." % (datetime.now(), customer_row.get('database-name'))
        else:
            if verbose > 1: print "%s Looking for entity id's." % (datetime.now()-d_start)
            entities_to_index = {}
            for property_row in property_table:
                entities_to_index[property_row.entity_id] = {'id': property_row.entity_id}
            if verbose > 1: print "%s There are %i unique entities to reindex." % (datetime.now()-d_start, len(entities_to_index))
            for entity in entities_to_index.values():
                db.execute(EQuery().searchindex(entity['id']))

        if verbose > 1: print "%s Entities reindexed." % (datetime.now()-d_start)


        processed_customers.setdefault(customer_row.get('database-name'), customer_row.get('database-name'))



        customer_finished_at = datetime.now()
        customer_time_spent = customer_finished_at - customer_started_at

        last_checked['_tq:metrics']['properties_checked'] = mov_ave * last_checked['_tq:metrics']['properties_checked'] + properties_to_check
        last_checked['_tq:metrics']['time_spent'] = mov_ave * last_checked['_tq:metrics']['time_spent'] + customer_time_spent.microseconds + (customer_time_spent.seconds + customer_time_spent.days * 86400) * 1000000


        with open(timestamp_file, 'w+') as f:
            f.write(json.dumps(last_checked, sort_keys=True, indent=4, separators=(',', ': ')))

    last_checked['_tq:metrics']['run_id'] = i + 1
    with open(timestamp_file, 'w+') as f:
        f.write(json.dumps(last_checked, sort_keys=True, indent=4, separators=(',', ': ')))


    known_customers = processed_customers

    d_stop = datetime.now()
    time_delta = d_stop - d_start
    time_spent_sec = 0.000001*time_delta.microseconds + time_delta.seconds + time_delta.days*86400
    sleep = time_spent_sec * sleepfactor + sleepfactor * 1
    print ".. %22s (%2.2f seconds). Now sleeping for %2.2f seconds." % (d_stop, time_spent_sec, sleep)
    print "Moving average (%1.2f) properties/second: %3.2f." % (mov_ave, 1000000.00*last_checked['_tq:metrics']['properties_checked']/last_checked['_tq:metrics']['time_spent'])
    time.sleep(sleep)
    # print json.dumps(customers, sort_keys=True, indent=4, separators=(',', ': '))















