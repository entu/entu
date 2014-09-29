import argparse
import time
import torndb
import yaml
import sys

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


reload(sys)
sys.setdefaultencoding('UTF-8')


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
             CONVERT(IF(
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
            ), CHAR) AS value
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
        LEFT JOIN property_definition ON property_definition.entity_definition_keyname = e.entity_definition_keyname AND property_definition.dataproperty IN ('database-host', 'database-name', 'database-user', 'database-password') AND property_definition.is_deleted = 0
        LEFT JOIN property ON property.property_definition_keyname = property_definition.keyname AND property.entity_id = e.id AND property.is_deleted = 0
        HAVING value IS NOT NULL;
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
        mongo_client.drop_database(self.db_name)
        mongo_db = mongo_client[self.db_name]
        # mongo_db = mongo_client['dev']
        self.mongo_collection = mongo_db['entity']

        # modulus.io
        # mongo_client = MongoClient('mongodb://import:eHFYUaN5CVFkVzdaUVxnmkbCMmbU2jC6@novus.modulusmongo.net:27017/wyvuxy8D')
        # mongo_db = mongo_client['wyvuxy8D']
        # self.mongo_collection = mongo_db[self.db_name]

        self.mongo_collection.create_index([('_mysql_id', 1), ('_mysql_db', 1)], name='mysql_id')
        # self.mongo_collection.create_index([('viewer', 1)], name='viewer')
        # self.mongo_collection.create_index([('parent', 1)], name='parent')
        # self.mongo_collection.create_index([('ancestor', 1)], name='ancestor')
        # self.mongo_collection.create_index([('definition', 1)], name='definition')
        # self.mongo_collection.create_index([('search.et', 1)], name='search_et')
        # self.mongo_collection.create_index([('search.en', 1)], name='search_en')


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
            -- WHERE e.entity_definition_keyname IN ('person', 'conf-menu-item', 'customer')
            ORDER BY
                e.id
            -- LIMIT 1000;
        """

        rows = self.db.query(sql)

        if args.verbose > 0: print '%s transfer %s entities' % (datetime.now(), len(rows))

        for r in rows:
            mysql_id = r.get('entity_id')

            # if self.mongo_collection.find_one({'_mysql_id': mysql_id, '_mysql_db': self.db_name}):
            #     continue

            e = {}
            e['_mysql_db'] = self.db_name
            e['_mysql_id'] = '%s' % mysql_id
            # if r.get('entity_old_id'):
            #     e['_mysql_old'] = '%s' % r.get('entity_old_id')

            e['_definition'] = r.get('entity_definition')
            e['_sharing']    = r.get('entity_sharing')
            e['_reference_property'] = [
                '_parent',
                '_ancestor',
                '_viewer',
                '_expander',
                '_editor',
                '_owner',
                '_created_by',
                '_changed_by',
                '_deleted_by',
            ]

            if r.get('entity_created'):
                e['_created_at'] = r.get('entity_created')
            if r.get('entity_created_by'):
                e['_created_by'] = '%s' % r.get('entity_created_by')

            if r.get('entity_changed'):
                e['_changed_at'] = r.get('entity_changed')
            if r.get('entity_changed_by'):
                e['_changed_by'] = '%s' % r.get('entity_changed_by')

            if r.get('entity_is_deleted') and r.get('entity_deleted'):
                e['_deleted_at'] = r.get('entity_deleted')
            if r.get('entity_is_deleted') and r.get('entity_deleted_by'):
                e['_deleted_by'] = '%s' % r.get('entity_deleted_by')

            viewers = self.__get_right(mysql_id, ['viewer', 'expander', 'editor', 'owner'])
            if viewers:
                e['_viewer'] = viewers

            expanders = self.__get_right(mysql_id, ['expander', 'editor', 'owner'])
            if expanders:
                e['_expander'] = expanders

            editors = self.__get_right(mysql_id, ['editor', 'owner'])
            if editors:
                e['_editor'] = editors

            owners = self.__get_right(mysql_id, ['owner'])
            if owners:
                e['_owner'] = owners

            parent = self.__get_parent(entity_id=mysql_id, recursive=False)
            if parent:
                e['_parent'] = parent

            ancestor = self.__get_parent(entity_id=mysql_id, recursive=True)
            if ancestor:
                e['_ancestor'] = ancestor

            sql = """
                SELECT
                    p.id                    AS property_id,
                    REPLACE(REPLACE(pd.dataproperty, '-', '_'), '.', '_')  AS property_dataproperty,
                    pd.datatype             AS property_datatype,
                    pd.formula              AS property_formula,
                    pd.search               AS property_search,
                    IF(pd.multilingual = 1, IF(p.language = 'english', 'en', 'et'), NULL) AS property_language,
                    TRIM(p.value_formula)   AS value_formula,
                    TRIM(p.value_string)    AS value_string,
                    TRIM(p.value_text)      AS value_text,
                    TRIM(p.value_display)   AS value_display,
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

                value = None
                if r2.get('property_formula') == 1 and r2.get('value_formula'):
                    value = {
                        'value': r2.get('value_formula')
                    }
                elif r2.get('property_datatype') == 'string' and r2.get('value_string'):
                    value = {
                        'value': r2.get('value_string')
                    }
                elif r2.get('property_datatype') == 'text' and r2.get('value_text'):
                    value = {
                        'value': r2.get('value_text')
                    }
                elif r2.get('property_datatype') == 'integer' and r2.get('value_integer') != None:
                    value = {
                        'value': r2.get('value_integer')
                    }
                elif r2.get('property_datatype') == 'decimal' and r2.get('value_decimal') != None:
                    value = {
                        'value': float(r2.get('value_decimal'))
                    }
                elif r2.get('property_datatype') == 'boolean' and r2.get('value_boolean') != None:
                    value = {
                        'value': bool(r2.get('value_boolean'))
                    }
                elif r2.get('property_datatype') in ['date', 'datetime'] and r2.get('value_datetime') != None:
                    value = {
                        'value': r2.get('value_datetime')
                    }
                elif r2.get('property_datatype') == 'reference' and r2.get('value_reference'):
                    value = {
                        'value': '%s' % r2.get('value_reference')
                    }
                    e.setdefault('_reference_property', []).append('property.%s' % r2.get('property_dataproperty'))
                elif r2.get('property_datatype') == 'file' and r2.get('value_file'):
                    value = {
                        'value': r2.get('value_file')
                    }
                    e.setdefault('_file_property', []).append(r2.get('property_dataproperty'))
                elif r2.get('property_datatype') == 'counter' and r2.get('value_string'):
                    value = {
                        'value': r2.get('value_counter')
                    }
                    e.setdefault('counter_property', []).append(r2.get('property_dataproperty'))
                elif r2.get('property_datatype') == 'counter-value' and r2.get('value_string'):
                    value = {
                        'value': r2.get('value_string')
                    }

                if not value:
                    continue

                value['type'] = r2.get('property_datatype')
                value['search'] = r2.get('property_search') == 1

                if r2.get('property_language'):
                    value['language'] = r2.get('property_language')

                e.setdefault(r2.get('property_dataproperty'), []).append(value)

                # if r2.get('value_display') and r2.get('property_search') == 1:
                #     if r2.get('property_language'):
                #         e.setdefault('_search', {}).setdefault(r2.get('property_language'), []).append(r2.get('value_display').lower())
                #     else:
                #         e.setdefault('_search', {}).setdefault('et', []).append(r2.get('value_display').lower())
                #         e.setdefault('_search', {}).setdefault('en', []).append(r2.get('value_display').lower())

            # for l in ['et', 'en']:
            #     if l in e.get('_search', {}):
            #         e['_search'][l] = list(set(e['_search'][l]))

            # for p_key, p_value in e.iteritems():
            #     if type(p_value) is dict:
            #         for v_key, v_value in p_value.iteritems():
            #             if type(e[p_key][v_key]) is list:
            #                 if len(e[p_key][v_key]) == 1:
            #                     e[p_key][v_key] = e[p_key][v_key][0]
            #     else:
            #         if type(e[p_key]) is list:
            #             if len(e[p_key]) == 1:
            #                 e[p_key] = e[p_key][0]

            #Create or replace Mongo object
            mongo_entity = self.mongo_collection.find_one({'_mysql_id': mysql_id, '_mysql_db': self.db_name}, {'_id': True})
            if mongo_entity:
                id = self.mongo_collection.update({'_id': mongo_entity.get('_id')}, e)
                if args.verbose > 3: print '%s -> %s (update)' % (mysql_id, mongo_entity.get('_id'))
            else:
                id = self.mongo_collection.insert(e)
                if args.verbose > 3: print '%s -> %s' % (mysql_id, id)

        self.stats['transfer_time'] = round((time.time() - t) / 60, 2)
        self.stats['transfer_speed'] = round(len(rows) / (time.time() - t), 2)


    def update(self):
        t = time.time()

        rows = self.mongo_collection.find({'_mysql_db': self.db_name})
        i = 0

        if args.verbose > 0: print '%s update %s entities' % (datetime.now(), rows.count())

        for e in rows:
            if args.verbose > 3: print '%s - %s' % (e['_mysql_db'], e.get('_id'))

            # reference properties
            for p in e.get('_reference_property', []):
                if type(e.get(p)) is dict:
                    for p_key, p_values in e.get(p, {}).iteritems():
                        mongo_references = []
                        for v in list(set(p_values)):
                            mongo_entity = self.mongo_collection.find_one({'_mysql_id': v, '_mysql_db': e['_mysql_db']}, {'_id': True})
                            if mongo_entity:
                                mongo_references.append(mongo_entity.get('_id'))
                                if args.verbose > 2: print '    %s reference %s.%s to %s' % (p, p_key, v, mongo_entity.get('_id'))
                        mongo_references = list(set(mongo_references))
                        if mongo_references:
                            id = self.mongo_collection.update({'_id': e.get('_id')}, {'$set': {'%s.%s' % (p, p_key): mongo_references}})
                elif type(e.get(p)) is list:
                    mongo_references = []
                    for v in list(set(e.get(p, []))):
                        mongo_entity = self.mongo_collection.find_one({'_mysql_id': v, '_mysql_db': e['_mysql_db']}, {'_id': True})
                        if mongo_entity:
                            mongo_references.append(mongo_entity.get('_id'))
                            if args.verbose > 2: print '    %s reference %s to %s' % (p, v, mongo_entity.get('_id'))
                    mongo_references = list(set(mongo_references))
                    if mongo_references:
                        id = self.mongo_collection.update({'_id': e.get('_id')}, {'$set': {'%s' % p: mongo_references}})
                else:
                    v = e.get(p)
                    mongo_entity = self.mongo_collection.find_one({'_mysql_id': v, '_mysql_db': e['_mysql_db']}, {'_id': True})
                    if mongo_entity:
                        id = self.mongo_collection.update({'_id': e.get('_id')}, {'$set': {'%s' % p: mongo_entity.get('_id')}})
                        if args.verbose > 2: print '    %s reference %s to %s' % (p, v, mongo_entity.get('_id'))

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
            entities.append('%s' % r.get('entity_id'))
            if recursive:
                entities = entities + self.__get_parent(entity_id=r.get('entity_id'), recursive=True)

        return list(set(entities))


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
            entities.append('%s' % r.get('related_entity_id'))

        return list(set(entities))



print '\n\n\n\n\n'
for c in customers():
    if c.get('database-name') not in ['www']:
        continue

    print '%s %s started' % (datetime.now(), c.get('database-name'))

    m2m = MySQL2MongoDB(
        db_host = c.get('database-host'),
        db_name = c.get('database-name'),
        db_user = c.get('database-user'),
        db_pass = c.get('database-password')
    )
    m2m.transfer()
    # m2m.update()

    print '%s %s ended' % (datetime.now(), c.get('database-name'))
    print '%s' % yaml.safe_dump(m2m.stats, default_flow_style=False, allow_unicode=True)
