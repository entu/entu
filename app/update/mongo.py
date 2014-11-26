import argparse
import os
import sys
import time
import torndb
import yaml

from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING
from operator import itemgetter




parser = argparse.ArgumentParser()
parser.add_argument('--host', default = '127.0.0.1')
parser.add_argument('--database', required = True)
parser.add_argument('--user', required = True)
parser.add_argument('--password', required = True)
parser.add_argument('--customergroup', required = False, default = '0')
parser.add_argument('-v', '--verbose', action = 'count', default = 0)
args = parser.parse_args()


reload(sys)
sys.setdefaultencoding('UTF-8')


def customers():
    db = torndb.Connection(
        host     = args.host,
        database = args.database,
        user     = args.user,
        password = args.password,
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
            -- AND relationship.entity_id IN (%s)
        ) AS e
        LEFT JOIN property_definition ON property_definition.entity_definition_keyname = e.entity_definition_keyname AND property_definition.dataproperty IN ('database-host', 'database-name', 'database-user', 'database-password') AND property_definition.is_deleted = 0
        LEFT JOIN property ON property.property_definition_keyname = property_definition.keyname AND property.entity_id = e.id AND property.is_deleted = 0
        HAVING value IS NOT NULL;
    """ % args.customergroup

    customers = {}
    for c in db.query(sql):
        if c.property in ['database-host', 'database-name', 'database-user', 'database-password']:
            if not c.value or not c.property:
                continue
            customers.setdefault(c.entity, {})[c.property] = c.value

    result = []
    for c, p in customers.iteritems():
        if not p.get('database-host') or not p.get('database-name') or not p.get('database-user') or not p.get('database-password'):
            continue

        try:
            db = torndb.Connection(
                host     = p.get('database-host'),
                database = p.get('database-name'),
                user     = p.get('database-user'),
                password = p.get('database-password'),
            )
            db.get('SELECT 1 FROM entity LIMIT 1;')
        except Exception:
            print p
            continue

        result.append(p)

    return sorted(result, key=itemgetter('database-name'))




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

        mongo_client = MongoClient('entu.cloudapp.net', 27017)
        mongo_db = mongo_client[self.db_name]
        # mongo_db = mongo_client['dev']
        self.mongo_collection = mongo_db['entity']
        self.mongo_collection.create_index([('_mysql.id', ASCENDING), ('_mysql.db', ASCENDING)])


    def transfer(self):
        # self.mongo_collection.drop()

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
            # if self.mongo_collection.find_one({'_mysql.id': '%s' % r.get('entity_id'), '_mysql.db': self.db_name}, {'_id': True}):
            #     continue

            mysql_id = r.get('entity_id')

            e = {}
            e.setdefault('_mysql', {})['id'] = '%s' % mysql_id
            e.setdefault('_mysql', {})['db'] = self.db_name

            e['_definition'] = r.get('entity_definition')

            if r.get('entity_created'):
                e.setdefault('_created', {})['date'] = r.get('entity_created')
            if r.get('entity_created_by'):
                e.setdefault('_created', {})['_id'] = '%s' % r.get('entity_created_by')
            if e.get('_created'):
                e['_created'] = [e.get('_created')]
                e.setdefault('_reference_property', []).append('_created')

            if r.get('entity_changed'):
                e.setdefault('_changed', {})['date'] = r.get('entity_changed')
            if r.get('entity_changed_by'):
                e.setdefault('_changed', {})['_id'] = '%s' % r.get('entity_changed_by')
            if e.get('_changed'):
                e['_changed'] = [e.get('_changed')]
                e.setdefault('_reference_property', []).append('_changed')

            if r.get('entity_is_deleted') and r.get('entity_deleted'):
                e.setdefault('_deleted', {})['date'] = r.get('entity_deleted')
            if r.get('entity_is_deleted') and r.get('entity_deleted_by'):
                e.setdefault('_deleted', {})['_id'] = '%s' % r.get('entity_deleted_by')
            if e.get('_deleted'):
                e['_deleted'] = [e.get('_deleted')]
                e.setdefault('_reference_property', []).append('_deleted')

            e.setdefault('_rights', {})['sharing']    = r.get('entity_sharing')

            viewers = self.__get_right(mysql_id, ['viewer', 'expander', 'editor', 'owner'])
            if viewers:
                e.setdefault('_rights', {})['viewer'] = [{'_id': x} for x in list(set(viewers))]
                e.setdefault('_reference_property', []).append('_rights.viewer')

            expanders = self.__get_right(mysql_id, ['expander', 'editor', 'owner'])
            if expanders:
                e.setdefault('_rights', {})['expander'] = [{'_id': x} for x in list(set(expanders))]
                e.setdefault('_reference_property', []).append('_rights.expander')

            editors = self.__get_right(mysql_id, ['editor', 'owner'])
            if editors:
                e.setdefault('_rights', {})['editor'] = [{'_id': x} for x in list(set(editors))]
                e.setdefault('_reference_property', []).append('_rights.editor')

            owners = self.__get_right(mysql_id, ['owner'])
            if owners:
                e.setdefault('_rights', {})['owner'] = [{'_id': x} for x in list(set(owners))]
                e.setdefault('_reference_property', []).append('_rights.owner')

            parent = self.__get_parent(entity_id=mysql_id, recursive=False)
            if parent:
                e['_parent'] = [{'_id': x} for x in list(set(parent))]
                e.setdefault('_reference_property', []).append('_parent')

            ancestor = self.__get_parent(entity_id=mysql_id, recursive=True)
            if ancestor:
                e['_ancestor'] = [{'_id': x} for x in list(set(ancestor))]
                e.setdefault('_reference_property', []).append('_ancestor')

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
                    IF(pd.datatype = 'file', (SELECT file FROM file WHERE id = p.value_file AND deleted IS NULL LIMIT 1), NULL) AS value_file,
                    IF(pd.datatype = 'file', (SELECT MD5(file) FROM file WHERE id = p.value_file AND deleted IS NULL LIMIT 1), NULL) AS value_file_md5,
                    IF(pd.datatype = 'file', (SELECT filename FROM file WHERE id = p.value_file AND deleted IS NULL LIMIT 1), NULL) AS value_file_name,
                    IF(pd.datatype = 'file', (SELECT LENGTH(file) FROM file WHERE id = p.value_file AND deleted IS NULL LIMIT 1), NULL) AS value_file_size,
                    IF(pd.datatype = 'file', (SELECT is_link FROM file WHERE id = p.value_file AND deleted IS NULL LIMIT 1), NULL) AS value_file_link,
                    p.value_counter
                FROM
                    property AS p,
                    property_definition AS pd
                WHERE pd.keyname = p.property_definition_keyname
                AND p.entity_id = %s
                AND p.is_deleted = 0
                AND pd.keyname NOT LIKE 'customer-database-%%'
                -- LIMIT 1000;
            """

            properties = {}
            for r2 in self.db.query(sql, mysql_id):

                value = None
                if r2.get('property_formula') == 1 and r2.get('value_formula'):
                    value = {'formula': r2.get('value_formula')}
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
                    value = {'_id': '%s' % r2.get('value_reference')}
                    e.setdefault('_reference_property', []).append('%s' % r2.get('property_dataproperty'))
                elif r2.get('property_datatype') == 'file' and r2.get('value_file'):
                    if r2.get('value_file_link') == 1:
                        value = {
                            'name': r2.get('value_file_name'),
                            'link': r2.get('file')
                        }
                    else:
                        value = {
                            'name': r2.get('value_file_name'),
                            'size': r2.get('value_file_size'),
                            'md5': r2.get('value_file_md5')
                        }
                elif r2.get('property_datatype') == 'counter' and r2.get('value_string'):
                    value = r2.get('value_counter')
                    e.setdefault('counter_property', []).append(r2.get('property_dataproperty'))
                elif r2.get('property_datatype') == 'counter-value' and r2.get('value_string'):
                    value = r2.get('value_string')

                if not value:
                    continue

                if r2.get('property_language'):
                    e.setdefault(r2.get('property_dataproperty'), {}).setdefault(r2.get('property_language'), []).append(value)
                else:
                    e.setdefault(r2.get('property_dataproperty'), []).append(value)

                if r2.get('value_display') and r2.get('property_search') == 1:
                    if r2.get('property_language'):
                        e.setdefault('_search', {}).setdefault(r2.get('property_language'), []).append(r2.get('value_display').lower())
                    else:
                        e.setdefault('_search', {}).setdefault('et', []).append(r2.get('value_display').lower())
                        e.setdefault('_search', {}).setdefault('en', []).append(r2.get('value_display').lower())

            for l in ['et', 'en']:
                if l in e.get('_search', {}):
                    e['_search'][l] = list(set(e['_search'][l]))

            #Create or replace Mongo object
            mongo_entity = self.mongo_collection.find_one({'_mysql.id': '%s' % mysql_id, '_mysql.db': self.db_name}, {'_id': True})
            if mongo_entity:
                id = self.mongo_collection.update({'_id': mongo_entity.get('_id')}, e)
                if args.verbose > 3: print '%s -> %s (update)' % (mysql_id, mongo_entity.get('_id'))
            else:
                id = self.mongo_collection.insert(e)
                if args.verbose > 3: print '%s -> %s' % (mysql_id, id)

        self.stats['transfer_time'] = round((time.time() - t) / 60, 2)
        self.stats['transfer_speed'] = round(len(rows) / (time.time() - t), 2)


    def update(self):
        self.mongo_collection.create_index([('_parent._id', ASCENDING)])
        self.mongo_collection.create_index([('_ancestor._id', ASCENDING)])
        self.mongo_collection.create_index([('_definition._id', ASCENDING)])
        self.mongo_collection.create_index([('_rights.viewer._id', ASCENDING)])
        self.mongo_collection.create_index([('_rights.sharing', ASCENDING)])
        self.mongo_collection.create_index([('_search.et', ASCENDING)])
        self.mongo_collection.create_index([('_search.en', ASCENDING)])

        t = time.time()

        rows = self.mongo_collection.find({'_mysql.db': self.db_name})
        i = 0

        if args.verbose > 0: print '%s update %s entities' % (datetime.now(), rows.count())

        for e in rows:
            if args.verbose > 3: print '%s - %s' % (e['_mysql']['db'], e.get('_id'))

            # reference properties
            for p in e.get('_reference_property', []):
                if '.' in p:
                    p_value = e.get(p.split('.')[0], {}).get(p.split('.')[1])
                else:
                    p_value = e.get(p)

                if type(p_value) is dict:
                    for p_key, p_values in p_value.iteritems():
                        mongo_references = []
                        for v in p_values:
                            mongo_entity = self.mongo_collection.find_one({'_mysql.id': v.get('_id'), '_mysql.db': e['_mysql']['db']}, {'_id': True})
                            if mongo_entity:
                                v['_id'] = mongo_entity.get('_id')
                                mongo_references.append(v)
                                if args.verbose > 2: print '    %s.%s reference to %s' % (p, p_key, v)
                        if mongo_references:
                            id = self.mongo_collection.update({'_id': e.get('_id')}, {'$set': {'%s.%s' % (p, p_key): mongo_references}})
                elif type(p_value) is list:
                    mongo_references = []
                    for v in p_value:
                        mongo_entity = self.mongo_collection.find_one({'_mysql.id': v.get('_id'), '_mysql.db': e['_mysql']['db']}, {'_id': True})
                        if mongo_entity:
                            v['_id'] = mongo_entity.get('_id')
                            mongo_references.append(v)
                            if args.verbose > 2: print '    %s reference to %s' % (p, v)
                    if mongo_references:
                        id = self.mongo_collection.update({'_id': e.get('_id')}, {'$set': {'%s' % p: mongo_references}})
                else:
                    mongo_entity = self.mongo_collection.find_one({'_mysql.id': p_value.get('_id'), '_mysql.db': e['_mysql']['db']}, {'_id': True})
                    if mongo_entity:
                        p_value['_id'] = mongo_entity.get('_id')
                        id = self.mongo_collection.update({'_id': e.get('_id')}, {'$set': {'%s' % p: p_value}})
                        if args.verbose > 2: print '    %s reference %s' % (p, p_value)

            self.mongo_collection.update({'_id': e.get('_id')}, {'$unset': {'_reference_property': 1}})

        self.stats['updates_time'] = round((time.time() - t) / 60, 2)
        self.stats['updates_speed'] = round(rows.count() / (time.time() - t), 2)


    def files(self):
        t = time.time()

        rows = self.db.query('SELECT file.id FROM file WHERE IFNULL(is_link, 0) <> 1 AND md5 IS NULL ORDER BY file.id;')

        if args.verbose > 0: print '%s transfer %s files' % (datetime.now(), len(rows))

        for r in rows:
            db_file = self.db.get('SELECT MD5(IFNULL(file.file,\'\')) AS md5, IFNULL(file.file, \'\') AS file FROM file WHERE id = %s LIMIT 1;', r.get('id'))
            if not db_file:
                continue
            if not db_file.get('md5'):
                continue

            directory = os.path.join('/', 'entu', 'files', self.db_name, db_file.get('md5')[0])
            filename = os.path.join(directory, db_file.get('md5'))

            if not os.path.exists(directory):
                os.makedirs(directory)
            f = open(filename, 'w')
            f.write(db_file.get('file'))
            f.close()

            if args.verbose > 2: print '%s -> %s' % (r.get('id'), db_file.get('md5'))

            self.db.execute('UPDATE file SET md5 = %s, file = NULL WHERE id = %s LIMIT 1;', db_file.get('md5'), r.get('id'))

        self.db.execute('OPTIMIZE TABLE file;')

        self.stats['files_time'] = round((time.time() - t) / 60, 2)
        # self.stats['files_speed'] = round(rows.count() / (time.time() - t), 2)


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
            entities.append('%s' % r.get('related_entity_id'))

        return entities



print '\n\n\n\n\n'
for c in customers():
    # if c.get('database-name') not in ['www']:
    #     continue

    # if c.get('database-name') < 'eka':
    #     continue

    print '%s %s started' % (datetime.now(), c.get('database-name'))

    m2m = MySQL2MongoDB(
        db_host = c.get('database-host'),
        db_name = c.get('database-name'),
        db_user = c.get('database-user'),
        db_pass = c.get('database-password')
    )
    # m2m.transfer()
    # m2m.update()
    m2m.files()

    print '%s %s ended' % (datetime.now(), c.get('database-name'))
    print '%s' % yaml.safe_dump(m2m.stats, default_flow_style=False, allow_unicode=True)
