import argparse
import time
import torndb

from datetime import datetime
from pymongo import MongoClient


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

    return customers.values()




class MySQL2MongoDB():
    def __init__(self, db_host, db_name, db_user, db_pass):
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
        self.start = None
        self.stats = {}


    def transfer2mongo(self):
        self.start = datetime.now()

        sql = """
                SELECT
                    REPLACE(REPLACE(e.entity_definition_keyname, '_', '-'), '.', '-') AS entity_definition,
                    e.id         AS entity_id,
                    e.sharing    AS entity_sharing,
                    IFNULL(e.created, (SELECT created FROM property WHERE entity_id = e.id ORDER BY id LIMIT 1))       AS entity_created,
                    IFNULL(e.created_by, (SELECT created_by FROM property WHERE entity_id = e.id ORDER BY id LIMIT 1)) AS entity_created_by,
                    -- (SELECT created FROM property WHERE entity_id = e.id ORDER BY id DESC LIMIT 1)                     AS entity_changed,
                    -- (SELECT created_by FROM property WHERE entity_id = e.id ORDER BY id DESC LIMIT 1)                  AS entity_changed_by,
                    e.is_deleted AS entity_is_deleted,
                    e.deleted    AS entity_deleted,
                    e.deleted_by AS entity_deleted_by,
                    e.old_id     AS entity_old_id,
                    p.id         AS property_id,
                    REPLACE(REPLACE(pd.dataproperty, '_', '-'), '.', '-')  AS property_dataproperty,
                    pd.datatype  AS property_datatype,
                    pd.formula   AS property_formula,
                    IF(p.language = 'estonian', 'et', IF(p.language = 'english', 'en', NULL)) AS property_language,
                    TRIM(p.value_formula) AS value_formula,
                    TRIM(p.value_string) AS value_string,
                    TRIM(p.value_text) AS value_text,
                    p.value_integer,
                    p.value_decimal,
                    p.value_boolean,
                    p.value_datetime,
                    p.value_reference,
                    p.value_file,
                    p.value_counter
                FROM
                    entity AS e,
                    property AS p,
                    property_definition AS pd
                WHERE p.entity_id = e.id
                AND pd.keyname = p.property_definition_keyname
                AND p.is_deleted = 0
                -- LIMIT 1000;
        """
        # logging.warning(sql)

        # Collect Entities from MySQL
        if args.verbose > 0: print '%s Collect Entities from MySQL' % datetime.now()
        i = 0
        t = time.time()
        entities = {}
        for r in self.db.query(sql):
            i += 1
            self.stats['properties'] = i
            self.stats['properties_avg'] = round(i / (time.time() - t), 2)
            if args.verbose > 1: print '%s - %s' % (r.get('entity_id'), r.get('property_dataproperty'))

            entities.setdefault(r.get('entity_id'), {}).setdefault('mysql', {})['db'] = self.db_name
            entities.setdefault(r.get('entity_id'), {}).setdefault('mysql', {})['id'] = '%s' % r.get('entity_id')
            if r.get('entity_old_id'):
                entities.setdefault(r.get('entity_id'), {}).setdefault('mysql', {})['old'] = r.get('entity_old_id')

            entities.setdefault(r.get('entity_id'), {})['definition'] = r.get('entity_definition')
            entities.setdefault(r.get('entity_id'), {})['sharing'] = r.get('entity_sharing')

            if r.get('entity_created'):
                entities.setdefault(r.get('entity_id'), {}).setdefault('created', {})['at'] = r.get('entity_created')
            if r.get('entity_created_by'):
                entities.setdefault(r.get('entity_id'), {}).setdefault('created', {})['by'] = '%s' % r.get('entity_created_by')

            if r.get('entity_changed'):
                entities.setdefault(r.get('entity_id'), {}).setdefault('changed', {})['at'] = r.get('entity_changed')
            if r.get('entity_changed_by'):
                entities.setdefault(r.get('entity_id'), {}).setdefault('changed', {})['by'] = '%s' % r.get('entity_changed_by')

            if r.get('entity_is_deleted') and r.get('entity_deleted'):
                entities.setdefault(r.get('entity_id'), {}).setdefault('deleted', {})['at'] = r.get('entity_deleted')
            if r.get('entity_is_deleted') and r.get('entity_deleted_by'):
                entities.setdefault(r.get('entity_id'), {}).setdefault('deleted', {})['by'] = '%s' % r.get('entity_deleted_by')

            if r.get('property_language'):
                p = entities.setdefault(r.get('entity_id'), {}).setdefault('property', {}).setdefault(r.get('property_dataproperty'), {}).setdefault(r.get('property_language'), [])
            else:
                p = entities.setdefault(r.get('entity_id'), {}).setdefault('property', {}).setdefault(r.get('property_dataproperty'), [])

            if r.get('property_formula') == 1 and r.get('value_formula'):
                p.append(r.get('value_formula'))
            elif r.get('property_datatype') == 'string' and r.get('value_string'):
                p.append(r.get('value_string'))
            elif r.get('property_datatype') == 'text' and r.get('value_text'):
                p.append(r.get('value_text'))
            elif r.get('property_datatype') == 'integer' and r.get('value_integer') != None:
                p.append(r.get('value_integer'))
            elif r.get('property_datatype') == 'decimal' and r.get('value_decimal') != None:
                p.append(float(r.get('value_decimal')))
            elif r.get('property_datatype') == 'boolean' and r.get('value_boolean') != None:
                p.append(bool(r.get('value_boolean')))
            elif r.get('property_datatype') in ['date', 'datetime'] and r.get('value_datetime') != None:
                p.append(r.get('value_datetime'))
            elif r.get('property_datatype') == 'reference' and r.get('value_reference'):
                p.append('%s' % r.get('value_reference'))
                entities.setdefault(r.get('entity_id'), {}).setdefault('reference_property', []).append(r.get('property_dataproperty'))
            elif r.get('property_datatype') == 'file' and r.get('value_file'):
                p.append('%s' % r.get('value_file'))
                entities.setdefault(r.get('entity_id'), {}).setdefault('file_property', []).append(r.get('property_dataproperty'))
            elif r.get('property_datatype') == 'counter' and r.get('value_string'):
                p.append(r.get('value_counter'))
                entities.setdefault(r.get('entity_id'), {}).setdefault('counter_property', []).append(r.get('property_dataproperty'))
            elif r.get('property_datatype') == 'counter-value' and r.get('value_string'):
                p.append(r.get('value_string'))


        # Insert Entities to MongoDB
        if args.verbose > 0: print '%s Insert Entities to MongoDB' % datetime.now()

        mongo_client = MongoClient('127.0.0.1', 27017)
        mongo_db = mongo_client['test']
        # mongo_db = mongo_client[self.db_name]
        mongo_collection = mongo_db['entity']

        i = 0
        t = time.time()
        for e in entities.values():
            i += 1
            self.stats['inserts'] = i
            self.stats['inserts_avg'] = round(i / (time.time() - t), 2)

            mysql_id = e.get('mysql', {}).get('id')

            viewers = self.__get_right(mysql_id, 'viewer')
            if viewers:
                e['viewer'] = viewers

            expanders = self.__get_right(mysql_id, 'expander')
            if expanders:
                e['expander'] = expanders

            editors = self.__get_right(mysql_id, 'editor')
            if editors:
                e['editor'] = editors

            owners = self.__get_right(mysql_id, 'owner')
            if owners:
                e['owner'] = owners

            parent = self.__get_parent(entity_id=mysql_id, recursive=False)
            if parent:
                e['parent'] = parent

            ancestor = self.__get_parent(entity_id=mysql_id, recursive=True)
            if ancestor:
                e['ancestor'] = ancestor

            for p_key, p_value in e.get('property', {}).iteritems():
                if type(p_value) is dict:
                    for v_key, v_value in p_value.iteritems():
                        e['property'][p_key][v_key] = list(set(v_value))
                else:
                    e['property'][p_key] = list(set(p_value))

            mongo_entity = mongo_collection.find_one({'mysql.id': mysql_id, 'mysql.db': self.db_name})
            if mongo_entity:
                id = mongo_collection.update({'_id': mongo_entity.get('_id')}, e)
                if args.verbose > 1: print '%s - replaced' % mongo_entity.get('_id')
            else:
                id = mongo_collection.insert(e)
                if args.verbose > 1: print '%s - created' % id

        # Replace MySQL FK's with MongoDB ID's
        if args.verbose > 0: print '%s Replace MySQL FK\'s with MongoDB ID\'s' % datetime.now()

        mongo_client = MongoClient('127.0.0.1', 27017)
        mongo_db = mongo_client['test']
        # mongo_db = mongo_client[self.db_name]
        mongo_collection = mongo_db['entity']

        i = 0
        t = time.time()
        for e in mongo_collection.find({'mysql.db': self.db_name}):
            i += 1
            self.stats['fk_replace_avg'] = round(i / (time.time() - t), 2)

            if args.verbose > 1: print '%s - %s' % (self.db_name, e.get('_id'))

            # creator, changer and deleter
            for x in ['created', 'changed', 'deleted']:
                mysql_id = e.get(x, {}).get('by')
                if mysql_id:
                    mongo_entity = mongo_collection.find_one({'mysql.id': mysql_id, 'mysql.db': self.db_name}, {'_id': 1})
                    if mongo_entity:
                        id = mongo_collection.update({'_id': e.get('_id')}, {'$set': {'%s.by' % x: mongo_entity.get('_id')}})
                        if args.verbose > 2: print '    %s.by %s to %s' % (x, mysql_id, mongo_entity.get('_id'))

            # parents, ancestors and viewers, expanders, editors, owners
            for x in ['parent', 'ancestor', 'viewer', 'expander', 'editor', 'owner']:
                mongo_id_list = []
                for mysql_id in list(set(e.get(x, []))):
                    mongo_entity = mongo_collection.find_one({'mysql.id': mysql_id, 'mysql.db': self.db_name}, {'_id': 1})
                    if mongo_entity:
                        mongo_id_list.append(mongo_entity.get('_id'))
                        if args.verbose > 2: print '    %s %s to %s' % (x, mysql_id, mongo_entity.get('_id'))
                if mongo_id_list:
                    id = mongo_collection.update({'_id': e.get('_id')}, {'$set': {x: mongo_id_list}})

            # reference properties
            for p in e.get('reference_property', []):
                if type(e.get('property', {}).get(p)) is dict:
                    for p_key, p_values in e.get('property', {}).get(p).iteritems():
                        mongo_references = []
                        for v in list(set(p_values)):
                            mongo_entity = mongo_collection.find_one({'mysql.id': v, 'mysql.db': self.db_name}, {'_id': 1})
                            if mongo_entity:
                                mongo_references.append(mongo_entity.get('_id'))
                                if args.verbose > 2: print '    %s reference %s.%s to %s' % (p, p_key, v, mongo_entity.get('_id'))
                        if mongo_references:
                            id = mongo_collection.update({'_id': e.get('_id')}, {'$set': {'property.%s.%s' % (p, p_key): mongo_references}})
                else:
                    mongo_references = []
                    for v in list(set(e.get('property', {}).get(p))):
                        mongo_entity = mongo_collection.find_one({'mysql.id': v, 'mysql.db': self.db_name}, {'_id': 1})
                        if mongo_entity:
                            mongo_references.append(mongo_entity.get('_id'))
                            if args.verbose > 2: print '    %s reference %s to %s' % (p, v, mongo_entity.get('_id'))
                    if mongo_references:
                        id = mongo_collection.update({'_id': e.get('_id')}, {'$set': {'property.%s' % p: mongo_references}})


    def __get_parent(self, entity_id, recursive=False):
        sql = """
            SELECT entity_id
            FROM relationship
            WHERE relationship_definition_keyname = 'child'
            AND is_deleted = 0
            AND entity_id IS NOT NULL
            AND related_entity_id = %s
        """ % entity_id
        # logging.warning(sql)

        entities = []
        for r in self.db.query(sql):
            entities.append('%s' % r.get('entity_id'))
            if recursive:
                entities = entities + self.__get_parent(entity_id=r.get('entity_id'), recursive=True)

        return entities


    def __get_right(self, entity_id, right):
        sql = """
            SELECT related_entity_id
            FROM relationship
            WHERE relationship_definition_keyname = '%s'
            AND is_deleted = 0
            AND related_entity_id IS NOT NULL
            AND entity_id = %s
        """ % (right, entity_id)
        # logging.warning(sql)

        entities = []
        for r in self.db.query(sql):
            entities.append('%s' % r.get('related_entity_id'))

        return entities




for c in customers():
    # if c.get('database-name') != 'eka':
    #     continue
    print '%s %s import started' % (datetime.now(), c.get('database-name'))
    m2m = MySQL2MongoDB(
        db_host = c.get('database-host'),
        db_name = c.get('database-name'),
        db_user = c.get('database-user'),
        db_pass = c.get('database-password')
    )
    m2m.transfer2mongo()
    print '%s' % m2m.stats
    print '%s %s import ended' % (datetime.now(), c.get('database-name'))
