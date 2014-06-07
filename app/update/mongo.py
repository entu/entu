import argparse
import time
import torndb
import yaml

from datetime import datetime
from pymongo import MongoClient
from operator import itemgetter




parser = argparse.ArgumentParser()
parser.add_argument('--database-host',     required = True)
parser.add_argument('--database-name',     required = True)
parser.add_argument('--database-user',     required = True)
parser.add_argument('--database-password', required = True)
parser.add_argument('--customergroup',     required = False, default = '0')
parser.add_argument('-v', '--verbose',     action = 'count', default = 0)
args = parser.parse_args()




def customers():
    db = torndb.Connection(
        host     = args.database_host,
        database = args.database_name,
        user     = args.database_user,
        password = args.database_password,
    )

    sql = """
        SELECT DISTINCT
            e.id AS entity,
            property_definition.dataproperty AS property,
            IF(
                property_definition.datatype='decimal',
                property.value_decimal,
                IF(
                    property_definition.datatype='integer',
                    property.value_integer,
                    IF(
                        property_definition.datatype='file',
                        property.value_file,
                        property.value_string
                    )
                )
            ) AS value
        FROM (
            SELECT
                entity.id,
                entity.entity_definition_keyname
            FROM
                entity,
                relationship
            WHERE relationship.related_entity_id = entity.id
            AND entity.is_deleted = 0
            AND relationship.is_deleted = 0
            AND relationship.relationship_definition_keyname = 'child'
            AND relationship.entity_id IN (%s)
        ) AS e
        LEFT JOIN property_definition ON property_definition.entity_definition_keyname = e.entity_definition_keyname AND property_definition.is_deleted = 0
        LEFT JOIN property ON property.property_definition_keyname = property_definition.keyname AND property.entity_id = e.id AND property.is_deleted = 0;
    """ % args.customergroup

    customers = {}
    for c in db.query(sql):
        if c.property in ['database-host', 'database-name', 'database-user', 'database-password']:
            customers.setdefault(c.entity, {})[c.property] = c.value

    return sorted(customers.values(), key=itemgetter('database-name'))




class MySQL2MongoDB():
    def __init__(self, db_host, db_name, db_user, db_pass):
        self.stats = {}

        self.db_host = db_host
        self.db_name = db_name
        self.db_user = db_user
        self.db_pass = db_pass
        self.db = torndb.Connection(
            host     = db_host,
            database = db_name,
            user     = db_user,
            password = db_pass,
        )

        mongo_client = MongoClient('mongo.entu.ee', 27017)
        mongo_db = mongo_client['test']
        # mongo_db = mongo_client[self.db_name]
        self.mongo_collection = mongo_db['entity']
        self.mongo_collection.create_index([('mysql.id', 1), ('mysql.db', 1)], name='mysqlIdx')
        # self.mongo_collection.create_index([('__search.value', 'text')], name='search_et_Idx', default_language='none', language_override='none')


    def transfer(self):
        t = time.time()

        sql = """
            SELECT
                REPLACE(REPLACE(e.entity_definition_keyname, '_', '-'), '.', '-') AS entity_definition,
                e.id         AS entity_id,
                e.sharing    AS entity_sharing,
                e.created    AS entity_created,
                e.created_by AS entity_created_by,
                e.is_deleted AS entity_is_deleted,
                e.deleted    AS entity_deleted,
                e.deleted_by AS entity_deleted_by,
                e.old_id     AS entity_old_id
            FROM
                entity AS e
            ORDER BY
                e.id
            -- LIMIT 1000;
        """

        rows = self.db.query(sql)

        if args.verbose > 0: print '%s transfer %s entities' % (datetime.now(), len(rows))

        for r in rows:
            mysql_id = r.get('entity_id')

            # if self.mongo_collection.find_one({'mysql.id': mysql_id, 'mysql.db': self.db_name}):
            #     continue

            e = {}
            e.setdefault('mysql', {})['db'] = self.db_name
            e.setdefault('mysql', {})['id'] = mysql_id
            if r.get('entity_old_id'):
                e.setdefault('mysql', {})['old'] = r.get('entity_old_id')

            e['definition'] = r.get('entity_definition')
            e['sharing'] = r.get('entity_sharing')

            if r.get('entity_created'):
                e.setdefault('created', {})['at'] = r.get('entity_created')
            if r.get('entity_created_by'):
                e.setdefault('created', {})['by'] = '%s' % r.get('entity_created_by')

            if r.get('entity_changed'):
                e.setdefault('changed', {})['at'] = r.get('entity_changed')
            if r.get('entity_changed_by'):
                e.setdefault('changed', {})['by'] = '%s' % r.get('entity_changed_by')

            if r.get('entity_is_deleted') and r.get('entity_deleted'):
                e.setdefault('deleted', {})['at'] = r.get('entity_deleted')
            if r.get('entity_is_deleted') and r.get('entity_deleted_by'):
                e.setdefault('deleted', {})['by'] = '%s' % r.get('entity_deleted_by')

            viewers = self.__get_right(mysql_id, ['viewer', 'expander', 'editor', 'owner'])
            if viewers:
                e['viewer'] = viewers

            expanders = self.__get_right(mysql_id, ['expander', 'editor', 'owner'])
            if expanders:
                e['expander'] = expanders

            editors = self.__get_right(mysql_id, ['editor', 'owner'])
            if editors:
                e['editor'] = editors

            owners = self.__get_right(mysql_id, ['owner'])
            if owners:
                e['owner'] = owners

            parent = self.__get_parent(entity_id=mysql_id, recursive=False)
            if parent:
                e['parent'] = parent

            ancestor = self.__get_parent(entity_id=mysql_id, recursive=True)
            if ancestor:
                e['ancestor'] = ancestor

            sql = """
                SELECT
                    p.id         AS property_id,
                    REPLACE(REPLACE(pd.dataproperty, '_', '-'), '.', '-')  AS property_dataproperty,
                    pd.datatype  AS property_datatype,
                    pd.formula   AS property_formula,
                    pd.search    AS property_search,
                    IF(pd.multilingual = 1, IF(p.language = 'english', 'en', 'et'), NULL) AS property_language,
                    TRIM(p.value_formula) AS value_formula,
                    TRIM(p.value_string) AS value_string,
                    TRIM(p.value_text) AS value_text,
                    TRIM(p.value_display) AS value_display,
                    p.value_integer,
                    p.value_decimal,
                    p.value_boolean,
                    p.value_datetime,
                    p.value_reference,
                    p.value_file,
                    p.value_counter
                FROM
                    property AS p,
                    property_definition AS pd
                WHERE pd.keyname = p.property_definition_keyname
                AND p.entity_id = %s
                AND p.is_deleted = 0
                -- LIMIT 1000;
            """ % mysql_id

            properties = {}
            for r2 in self.db.query(sql):

                e['_reference_property'] = ['parent', 'ancestor', 'viewer', 'expander', 'editor', 'owner']

                value = None
                if r2.get('property_formula') == 1 and r2.get('value_formula'):
                    value = r2.get('value_formula')
                elif r2.get('property_datatype') == 'string' and r2.get('value_string'):
                    value = r2.get('value_string')
                elif r2.get('property_datatype') == 'text' and r2.get('value_text'):
                    value = r2.get('value_text')
                elif r2.get('property_datatype') == 'integer' and r2.get('value_integer') != None:
                    value = r2.get('value_integer')
                elif r2.get('property_datatype') == 'decimal' and r2.get('value_decimal') != None:
                    value = float(r2.get('value_decimal'))
                elif r2.get('property_datatype') == 'boolean' and r2.get('value_boolean') != None:
                    value = bool(r2.get('value_boolean'))
                elif r2.get('property_datatype') in ['date', 'datetime'] and r2.get('value_datetime') != None:
                    value = r2.get('value_datetime')
                elif r2.get('property_datatype') == 'reference' and r2.get('value_reference'):
                    value = r2.get('value_reference')
                    e.setdefault('_reference_property', []).append(r2.get('property_dataproperty'))
                elif r2.get('property_datatype') == 'file' and r2.get('value_file'):
                    value = r2.get('value_file')
                    e.setdefault('_file_property', []).append(r2.get('property_dataproperty'))
                elif r2.get('property_datatype') == 'counter' and r2.get('value_string'):
                    value = r2.get('value_counter')
                    e.setdefault('counter_property', []).append(r2.get('property_dataproperty'))
                elif r2.get('property_datatype') == 'counter-value' and r2.get('value_string'):
                    value = r2.get('value_string')

                if r2.get('property_language'):
                    properties.setdefault(r2.get('property_dataproperty'), {}).setdefault(r2.get('property_language'), []).append(value)
                else:
                    properties.setdefault(r2.get('property_dataproperty'), []).append(value)

                if r2.get('value_display') and r2.get('property_search') == 1:
                    if r2.get('property_language'):
                        e.setdefault('_search', {}).setdefault(r2.get('property_language'), []).append(r2.get('value_display').lower())
                    else:
                        e.setdefault('_search', {}).setdefault('et', []).append(r2.get('value_display').lower())
                        e.setdefault('_search', {}).setdefault('en', []).append(r2.get('value_display').lower())

            for p_key, p_value in properties.iteritems():
                if type(p_value) is dict:
                    for v_key, v_value in p_value.iteritems():
                        e.setdefault(p_key, {})[v_key] = list(set(v_value))
                else:
                    e[p_key] = list(set(p_value))

            for l in ['et', 'en']:
                if l in e.get('_search', {}):
                    e['_search'][l] = list(set(e['_search'][l]))

            #Create or replace Mongo object
            mongo_entity = self.mongo_collection.find_one({'mysql.id': mysql_id, 'mysql.db': self.db_name}, {'_id': True})
            if mongo_entity:
                id = self.mongo_collection.update({'_id': mongo_entity.get('_id')}, e)
                if args.verbose > 1: print '%s -> %s (update)' % (mysql_id, mongo_entity.get('_id'))
            else:
                id = self.mongo_collection.insert(e)
                if args.verbose > 1: print '%s -> %s' % (mysql_id, id)

        self.stats['transfer_time'] = round((time.time() - t) / 60, 2)
        self.stats['transfer_speed'] = round(len(rows) / (time.time() - t), 2)


    def update(self):
        t = time.time()

        rows = self.mongo_collection.find({'mysql.db': self.db_name})
        i = 0

        if args.verbose > 0: print '%s update %s entities' % (datetime.now(), rows.count())

        for e in rows:
            db_name = e['mysql']['db']

            if args.verbose > 1: print '%s - %s' % (db_name, e.get('_id'))

            # creator, changer and deleter
            for x in ['created', 'changed', 'deleted']:
                mysql_id = e.get(x, {}).get('by')
                if mysql_id:
                    mongo_entity = self.mongo_collection.find_one({'mysql.id': mysql_id, 'mysql.db': db_name}, {'_id': True})
                    if mongo_entity:
                        id = self.mongo_collection.update({'_id': e.get('_id')}, {'$set': {'%s.by' % x: mongo_entity.get('_id')}})
                        if args.verbose > 2: print '    %s.by %s to %s' % (x, mysql_id, mongo_entity.get('_id'))

            # reference properties
            for p in e.get('_reference_property', []):
                if type(e.get(p)) is dict:
                    for p_key, p_values in e.get(p, {}).iteritems():
                        mongo_references = []
                        for v in list(set(p_values)):
                            mongo_entity = self.mongo_collection.find_one({'mysql.id': v, 'mysql.db': db_name}, {'_id': True})
                            if mongo_entity:
                                mongo_references.append(mongo_entity.get('_id'))
                                if args.verbose > 2: print '    %s reference %s.%s to %s' % (p, p_key, v, mongo_entity.get('_id'))
                        mongo_references = list(set(mongo_references))
                        if mongo_references:
                            id = self.mongo_collection.update({'_id': e.get('_id')}, {'$set': {'%s.%s' % (p, p_key): mongo_references}})
                else:
                    mongo_references = []
                    for v in list(set(e.get(p, []))):
                        mongo_entity = self.mongo_collection.find_one({'mysql.id': v, 'mysql.db': db_name}, {'_id': True})
                        if mongo_entity:
                            mongo_references.append(mongo_entity.get('_id'))
                            if args.verbose > 2: print '    %s reference %s to %s' % (p, v, mongo_entity.get('_id'))
                    mongo_references = list(set(mongo_references))
                    if mongo_references:
                        id = self.mongo_collection.update({'_id': e.get('_id')}, {'$set': {'%s' % p: mongo_references}})

            self.mongo_collection.update({'_id': e.get('_id')}, {'$unset': {'_reference_property': 1}})
            # self.mongo_collection.update({'_id': e.get('_id')}, {'$unset': {'_file_property': 1}})

        self.stats['updates_time'] = round((time.time() - t) / 60, 2)
        self.stats['updates_speed'] = round(rows.count() / (time.time() - t), 2)


    def __get_parent(self, entity_id, recursive=False):
        sql = """
            SELECT entity_id
            FROM relationship
            WHERE relationship_definition_keyname = 'child'
            AND is_deleted = 0
            AND entity_id IS NOT NULL
            AND related_entity_id = %s
        """ % entity_id

        entities = []
        for r in self.db.query(sql):
            entities.append(r.get('entity_id'))
            if recursive:
                entities = entities + self.__get_parent(entity_id=r.get('entity_id'), recursive=True)

        return entities


    def __get_right(self, entity_id, rights):
        sql = """
            SELECT related_entity_id
            FROM relationship
            WHERE relationship_definition_keyname IN (%s)
            AND is_deleted = 0
            AND related_entity_id IS NOT NULL
            AND entity_id = %s
        """ % (', '.join(['\'%s\'' % x for x in rights]), entity_id)

        entities = []
        for r in self.db.query(sql):
            entities.append(r.get('related_entity_id'))

        return list(set(entities))



print '\n\n\n\n\n'
for c in customers():
    if c.get('database-name') in ['dev', 'devm', 'tftak']:
        continue

    print '%s %s started' % (datetime.now(), c.get('database-name'))

    m2m = MySQL2MongoDB(
        db_host = c.get('database-host'),
        db_name = c.get('database-name'),
        db_user = c.get('database-user'),
        db_pass = c.get('database-password')
    )
    m2m.transfer()
    m2m.update()

    print '%s %s ended' % (datetime.now(), c.get('database-name'))
    print '%s' % yaml.safe_dump(m2m.stats, default_flow_style=False, allow_unicode=True)
