# maintenance.py

# - Get chunk of newly created or deleted properties
# - Revaluate formulas
#   - For new formula property calculate it's value
#   - For any parent entity recalculate formulas affected by property
#   - For any child entity recalculate formulas affected by property
#   - For "self" entity recalculate formulas affected by property
#   - For back-referencing entity recalculate formulas affected by property
# - Populate value_display
# - Get entities for affected properties
# - Reindex entity_info

from datetime import datetime
import argparse
import yaml
import json
import time

from etask import *


parser = argparse.ArgumentParser()
parser.add_argument('--database-host',     required = True)
parser.add_argument('--database-name',     required = True)
parser.add_argument('--database-user',     required = True)
parser.add_argument('--database-password', required = True)
parser.add_argument('--customergroup',     required = False, default = '0')
parser.add_argument('-v', '--verbose',     action = 'count')
args = parser.parse_args()

# Set verbosity level
verbose = 0
if args.verbose:
    verbose = args.verbose

timestamp_file = 'maintenance.yaml'
last_checked = {}
try:
    with open(timestamp_file, 'r+') as f:
        last_checked = yaml.load(f.read())
except IOError as e:
    print "\n\n%s No timestamp file '%s'." % (datetime.now(), timestamp_file)

task = ETask(args)

i = 0
sleepfactor = 0.25
mov_ave = 0.99
chunk_size = 1000
min_date = '1900-01-01 00:00:00'

while True:
    d_start = datetime.now()
    i = last_checked.setdefault('_metrics', {}).setdefault('run_id', 0)

    print "\n\n%s" % (d_start)

    task.reload_customers()

    for customer_row in task.customers.values():
        log_messages = []
        cdb = torndb.Connection(
            host     = customer_row.get('database-host')[0],
            database = customer_row.get('database-name')[0],
            user     = customer_row.get('database-user')[0],
            password = customer_row.get('database-password')[0],
        )
        customer_languages = customer_row.get('language-ref')

        # last_checked.setdefault(customer_row.get('domain')[0], {}).setdefault('last_id', 0)
        last_checked.setdefault(customer_row.get('domain')[0], {}).setdefault('latest_checked', min_date)
        last_checked.setdefault('_metrics', {}).setdefault('properties_checked', 0.0000)
        last_checked.setdefault('_metrics', {}).setdefault('time_spent', 0.0000)

        customer_started_at = datetime.now()
        if verbose > 0: log_messages.append("\n%s Starting for --== %s ==--." % (datetime.now(), customer_row.get('domain')[0]))

        check_time = last_checked[customer_row.get('domain')[0]]['latest_checked']
        if check_time == min_date:
            if verbose > 0: log_messages.append("%s Initial run - evaluating all formulas." % (datetime.now()-customer_started_at))
            print "\n".join(log_messages)
            property_table = cdb.query(EQuery().all_formula_properties())
        else:
            if verbose > 1: log_messages.append("%s Looking for properties fresher than %s." % (datetime.now()-customer_started_at, check_time))
            property_table = cdb.query(EQuery().fresh_properties(chunk_size, check_time, False))
            properties_to_check = len(property_table)
            if properties_to_check == 0:
                continue
            print "\n".join(log_messages)
            if properties_to_check < chunk_size:
                if verbose > 2: print "%s Got %s properties." % (datetime.now()-customer_started_at, properties_to_check)
            else: # If chunk size of rows returned, then reload query with next second properties only.
                first_second = property_table[0].o_date
                last_second = property_table[chunk_size-1].o_date
                if verbose > 2: print "%s Reloading properties with timestamp between %s and %s inclusive." % (datetime.now()-customer_started_at, first_second, last_second)
                property_table = cdb.query(EQuery().fresh_properties(chunk_size, first_second, last_second))
                properties_to_check = len(property_table)
                if verbose > 2: print "%s Got %s properties with timestamp between %s and %s inclusive." % (datetime.now()-customer_started_at, properties_to_check, first_second, last_second)

        # Property revaluation
        if verbose > 0: print "%s Checking %i properties." % (datetime.now()-customer_started_at, len(property_table))
        for property_row in property_table:
            # raw_input('Press enter 1')
            if property_row.value_formula:
                # raw_input('Press enter 2')
                task.evaluate_formula(cdb, property_row)
            task.update_related_formulas(cdb, property_row, [])
        if verbose > 3: print "%s %i properties checked." % (datetime.now()-customer_started_at, len(property_table))

        # Deleted entities
        cdb.execute(EQuery().delete_referencing_properties(), property_table[0].o_date, property_table[len(property_table)-1].o_date)
        # for property_row in cdb.execute(EQuery().delete_referencing_properties(), first_second, last_second):
        #     task.evaluate_formula(cdb, property_row)
        #     task.update_related_formulas(cdb, property_row, [])



        # wrap it up
        last_checked[customer_row.get('domain')[0]]['latest_checked'] = property_table[len(property_table)-1].o_date
        customer_finished_at = datetime.now()
        customer_time_spent = customer_finished_at - customer_started_at

        last_checked['_metrics']['properties_checked'] = mov_ave * last_checked['_metrics']['properties_checked'] + properties_to_check
        last_checked['_metrics']['time_spent'] = mov_ave * last_checked['_metrics']['time_spent'] + customer_time_spent.microseconds + (customer_time_spent.seconds + customer_time_spent.days * 86400) * 1000000

        with open(timestamp_file, 'w+') as f:
            f.write(yaml.safe_dump(last_checked, default_flow_style=False, allow_unicode=True))

    with open(timestamp_file, 'w+') as f:
        f.write(yaml.safe_dump(last_checked, default_flow_style=False, allow_unicode=True))

    d_stop = datetime.now()
    time_delta = d_stop - d_start
    time_spent_sec = 0.000001*time_delta.microseconds + time_delta.seconds + time_delta.days*86400
    sleep = min(time_spent_sec * sleepfactor + sleepfactor * 1, sleepfactor * 20)
    print "%s (%2.2f seconds). Now sleeping for %2.2f seconds." % (d_stop, time_spent_sec, sleep)
    print "Moving average (%1.2f) properties/second: %3.2f." % (
        mov_ave,
        1000000.00*last_checked['_metrics']['properties_checked']/last_checked['_metrics']['time_spent'])
    time.sleep(sleep)

    if verbose > 4: raw_input('Press enter')
