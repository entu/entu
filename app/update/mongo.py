import os
import sys
import time
import torndb

from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING
from operator import itemgetter



APP_MONGODB        = os.getenv('MONGODB', 'mongodb://localhost:27017/')
APP_MYSQL_HOST     = os.getenv('MYSQL_HOST', 'localhost')
APP_MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')
APP_MYSQL_USER     = os.getenv('MYSQL_USER')
APP_MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')



reload(sys)
sys.setdefaultencoding('UTF-8')


def customers():
    db = torndb.Connection(
        host     = APP_MYSQL_HOST,
        database = APP_MYSQL_DATABASE,
        user     = APP_MYSQL_USER,
        password = APP_MYSQL_PASSWORD,
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
        ) AS e
        LEFT JOIN property_definition ON property_definition.entity_definition_keyname = e.entity_definition_keyname AND property_definition.dataproperty IN ('database-host', 'database-name', 'database-user', 'database-password') AND property_definition.is_deleted = 0
        LEFT JOIN property ON property.property_definition_keyname = property_definition.keyname AND property.entity_id = e.id AND property.is_deleted = 0
        HAVING value IS NOT NULL;
    """

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
        if self.db_name == 'www':
            self.mongo_db = MongoClient(APP_MONGODB)['entu']
        else:
            self.mongo_db = MongoClient(APP_MONGODB)[self.db_name]

        self.mongo_db.entityVersion.create_index([('_mid', ASCENDING)])


    def transfer(self):
        # self.mongo_collection.drop()

        t = time.time()

        actions_sql = """
            SELECT
                entity_id,
                (SELECT entity_definition_keyname FROM entity WHERE id = entity_id LIMIT 1) AS definition,
                (SELECT sharing FROM entity WHERE id = entity_id LIMIT 1) AS sharing,
                IFNULL(dt, (SELECT created FROM entity WHERE id = entity_id LIMIT 1)) AS dt,
                person,
                GROUP_CONCAT(action ORDER BY action SEPARATOR ',') AS action
            FROM (
                -- PROPERTY ADD
                SELECT
                	entity_id,
                	IF(created > '1900', created, NULL) AS dt,
                	IF(CAST(created_by AS UNSIGNED) > 0, CAST(created_by AS UNSIGNED), NULL) AS person,
                	'change' AS action
                FROM property
                GROUP BY entity_id, created, created_by

                -- PROPERTY DELETE
                UNION SELECT
                	entity_id,
                	IF(deleted > '1900', deleted, NULL) AS dt,
                	IF(CAST(deleted_by AS UNSIGNED) > 0, CAST(deleted_by AS UNSIGNED), NULL) AS person,
                	'change' AS action
                FROM property
                WHERE is_deleted = 1
                GROUP BY entity_id, deleted, deleted_by

                -- ENTITY DELETE
                -- UNION SELECT
                -- 	id AS entity_id,
                -- 	IF(deleted > '1900', deleted, NULL) AS dt,
                -- 	IF(CAST(deleted_by AS UNSIGNED) > 0, CAST(deleted_by AS UNSIGNED), NULL) AS person,
                -- 	'delete' AS action
                -- FROM entity
                -- WHERE is_deleted = 1
                -- GROUP BY deleted, deleted_by

                -- PARENT ADD
                UNION SELECT
                	related_entity_id AS entity_id,
                	IF(created > '1900', created, NULL) AS dt,
                	IF(CAST(created_by AS UNSIGNED) > 0, CAST(created_by AS UNSIGNED), NULL) AS person,
                	'parent' AS action
                FROM relationship
                WHERE relationship_definition_keyname = 'child'
                GROUP BY related_entity_id, created, created_by

                -- PARENT DELETED
                UNION SELECT
                	related_entity_id AS entity_id,
                	IF(deleted > '1900', deleted, NULL) AS dt,
                	IF(CAST(deleted_by AS UNSIGNED) > 0, CAST(deleted_by AS UNSIGNED), NULL) AS person,
                	'parent' AS action
                FROM relationship
                WHERE is_deleted = 1
                AND relationship_definition_keyname = 'child'
                GROUP BY related_entity_id, deleted, deleted_by

                -- RIGHT ADD
                UNION SELECT
                	entity_id,
                	IF(created > '1900', created, NULL) AS dt,
                	IF(CAST(created_by AS UNSIGNED) > 0, CAST(created_by AS UNSIGNED), NULL) AS person,
                	'right' AS action
                FROM relationship
                WHERE relationship_definition_keyname IN ('viewer', 'expander', 'editor', 'owner')
                GROUP BY entity_id, created, created_by

                -- RIGHT DELETED
                UNION SELECT
                	entity_id,
                	IF(deleted > '1900', deleted, NULL) AS dt,
                	IF(CAST(deleted_by AS UNSIGNED) > 0, CAST(deleted_by AS UNSIGNED), NULL) AS person,
                	'right' AS action
                FROM relationship
                WHERE is_deleted = 1
                AND relationship_definition_keyname IN ('viewer', 'expander', 'editor', 'owner')
                GROUP BY entity_id, deleted, deleted_by
            ) AS x
            WHERE entity_id IN (SELECT entity_id FROM property)
            GROUP BY
                definition,
                entity_id,
                dt,
                person
            ORDER BY
                definition,
                entity_id,
                dt,
                person,
                action
        """

        rows = self.db.query(actions_sql)

        print '%s transfer %s entity versions' % (datetime.now(), len(rows))

        for r in rows:
            mysql_id = r.get('entity_id')

            e = {}
            e['_mid'] = mysql_id
            e['_definition'] = r.get('definition')
            e['_sharing'] = r.get('sharing')

            if r.dt:
                e.setdefault('_created', {})['at'] = r.get('entity_created')
            if r.person:
                e.setdefault('_created', {})['by'] = r.get('entity_created_by')
            if e.get('_created'):
                e['_created']['type'] = 'action'
                e['_created'] = [e.get('_created')]

            # if r.get('entity_changed'):
            #     e.setdefault('_changed', {})['at'] = r.get('entity_changed')
            # if r.get('entity_changed_by'):
            #     e.setdefault('_changed', {})['by'] = r.get('entity_changed_by')
            # if e.get('_changed'):
            #     e['_changed']['type'] = 'action'
            #     e['_changed'] = [e.get('_changed')]
            #
            # if r.get('entity_is_deleted') and r.get('entity_deleted'):
            #     e.setdefault('_deleted', {})['at'] = r.get('entity_deleted')
            # if r.get('entity_is_deleted') and r.get('entity_deleted_by'):
            #     e.setdefault('_deleted', {})['by'] = r.get('entity_deleted_by')
            # if e.get('_deleted'):
            #     e['_deleted']['type'] = 'action'
            #     e['_deleted'] = [e.get('_deleted')]
            #
            # viewers = self.__get_mongodb_right(mysql_id, ['viewer', 'expander', 'editor', 'owner'], p.created)
            # if viewers:
            #     e['_viewer'] = [{'reference': x, 'type': 'reference'} for x in list(set(viewers))]
            #
            # expanders = self.__get_mongodb_right(mysql_id, ['expander', 'editor', 'owner'], p.created)
            # if expanders:
            #     e['_expander'] = [{'reference': x, 'type': 'reference'} for x in list(set(expanders))]
            #
            # editors = self.__get_mongodb_right(mysql_id, ['editor', 'owner'], p.created)
            # if editors:
            #     e['_editor'] = [{'reference': x, 'type': 'reference'} for x in list(set(editors))]
            #
            # owners = self.__get_mongodb_right(mysql_id, ['owner'], p.created)
            # if owners:
            #     e['_owner'] = [{'reference': x, 'type': 'reference'} for x in list(set(owners))]
            #
            # parent = self.__get_mongodb_parent(entity_id=mysql_id, recursive=False, p.created)
            # if parent:
            #     e['_parent'] = [{'reference': x, 'type': 'reference'} for x in list(set(parent))]
            #
            # ancestor = self.__get_mongodb_parent(entity_id=mysql_id, recursive=True, p.created)
            # if ancestor:
            #     e['_ancestor'] = [{'reference': x, 'type': 'reference'} for x in list(set(ancestor))]

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
                    IF(pd.datatype = 'file', (SELECT s3_key FROM file WHERE id = p.value_file AND deleted IS NULL LIMIT 1), NULL) AS value_file_s3,
                    IF(pd.datatype = 'file', (SELECT md5 FROM file WHERE id = p.value_file AND deleted IS NULL LIMIT 1), NULL) AS value_file_md5,
                    IF(pd.datatype = 'file', (SELECT filename FROM file WHERE id = p.value_file AND deleted IS NULL LIMIT 1), NULL) AS value_file_name,
                    IF(pd.datatype = 'file', (SELECT filesize FROM file WHERE id = p.value_file AND deleted IS NULL LIMIT 1), NULL) AS value_file_size,
                    IF(pd.datatype = 'file', (SELECT url FROM file WHERE id = p.value_file AND deleted IS NULL LIMIT 1), NULL) AS value_file_url,
                    p.value_counter,
                    p.created,
                    IF(CAST(p.created_by AS UNSIGNED) > 0, CAST(p.created_by AS UNSIGNED), NULL) AS created_by,
                    p.is_deleted,
                    p.deleted,
                    IF(CAST(p.deleted_by AS UNSIGNED) > 0, CAST(p.deleted_by AS UNSIGNED), NULL) AS deleted_by
                FROM
                    property AS p,
                    property_definition AS pd
                WHERE pd.keyname = p.property_definition_keyname
                AND p.entity_id = %s
            """ % mysql_id
            if r.dt:
                sql += """
                    AND (p.created IS NULL OR p.created <= '%s')
                    AND (p.deleted IS NULL OR p.deleted > '%s')
                """ % (r.dt, r.dt)

            if r.person:
                sql += """
                    AND p.created_by = %s
                """ % r.person
            else:
                sql += """
                    AND p.created_by IS NULL
                """

            sql += """
                AND pd.dataproperty NOT IN ('entu-changed-by', 'entu-changed-at', 'entu-created-by', 'entu-created-at')
                AND pd.dataproperty NOT LIKE 'auth_%%'
                AND pd.datatype NOT IN ('counter')
                AND pd.formula = 0;
            """

            properties = {}
            for r2 in self.db.query(sql):
                value = {}

                if r2.get('property_datatype') == 'string' and r2.get('value_string'):
                    value['value'] = r2.get('value_string')
                elif r2.get('property_datatype') == 'text' and r2.get('value_text'):
                    value['value'] = r2.get('value_text')
                elif r2.get('property_datatype') == 'integer' and r2.get('value_integer') != None:
                    value['value'] = r2.get('value_integer')
                elif r2.get('property_datatype') == 'decimal' and r2.get('value_decimal') != None:
                    value['value'] = float(r2.get('value_decimal'))
                elif r2.get('property_datatype') == 'boolean' and r2.get('value_boolean') != None:
                    value['value'] = bool(r2.get('value_boolean'))
                elif r2.get('property_datatype') in ['date', 'datetime'] and r2.get('value_datetime') != None:
                    value['value'] = r2.get('value_datetime')
                elif r2.get('property_datatype') == 'reference' and r2.get('value_reference'):
                    value['reference'] = r2.get('value_reference')
                elif r2.get('property_datatype') == 'counter-value' and r2.get('value_string'):
                    value['value'] = r2.get('value_string')
                elif r2.get('property_datatype') == 'file' and r2.get('value_file'):
                    value['value'] = r2.get('value_file_name')
                    if r2.get('value_file_url'):
                        value['url'] = r2.get('file')
                    else:
                        value['size'] = r2.get('value_file_size')
                        if r2.get('value_file_md5', None):
                            value['md5'] = r2.get('value_file_md5')
                        if r2.get('value_file_s3', None):
                            value['s3'] = r2.get('value_file_s3')

                if not value:
                    continue

                value['_mid'] = r2.get('property_id')
                value['type'] = r2.get('property_datatype')

                if r2.get('property_language'):
                    value['language'] = r2.get('property_language')

                # if r2.get('created'):
                #     value.setdefault('created', {})['at'] = r2.get('created')
                # if r2.get('created_by'):
                #     value.setdefault('created', {})['by'] = r2.get('created_by')
                #
                # if r2.get('is_deleted') and r2.get('deleted'):
                #     value.setdefault('deleted', {})['at'] = r2.get('deleted')
                # if r2.get('is_deleted') and r2.get('deleted_by'):
                #     value.setdefault('deleted', {})['by'] = r2.get('deleted_by')

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

            #Create or replace Mongo object
            try:
                mongo_entity_version = self.mongo_db.entityVersion.find_one({'_mid': mysql_id}, {'_id': False, '_entity': True})
                if mongo_entity_version:
                    e['_entity'] = mongo_entity_version.get('_entity')
                else:
                    e['_entity'] = self.mongo_db.entity.insert_one({}).inserted_id
                self.mongo_db.entityVersion.insert_one(e)
            except Exception, err:
                print 'MongoDb error: %s - %s' % (err, e)



    # def update(self):
    #     self.mongo_collection.create_index([('_parent._id', ASCENDING)])
    #     self.mongo_collection.create_index([('_ancestor._id', ASCENDING)])
    #     self.mongo_collection.create_index([('_definition._id', ASCENDING)])
    #     self.mongo_collection.create_index([('_viewer._id', ASCENDING)])
    #     self.mongo_collection.create_index([('_sharing', ASCENDING)])
    #     self.mongo_collection.create_index([('_search.et', ASCENDING)])
    #     self.mongo_collection.create_index([('_search.en', ASCENDING)])
    #
    #     t = time.time()
    #
    #     rows = self.mongo_collection.find()
    #     i = 0
    #
    #     print '%s update %s entities' % (datetime.now(), rows.count())
    #
    #     for e in rows:
    #         # reference properties
    #         for p in e.get('_reference_property', []):
    #             if '.' in p:
    #                 p_value = e.get(p.split('.')[0], {}).get(p.split('.')[1])
    #             else:
    #                 p_value = e.get(p)
    #
    #             if type(p_value) is dict:
    #                 for p_key, p_values in p_value.iteritems():
    #                     mongo_references = []
    #                     for v in p_values:
    #                         mongo_entity = self.mongo_collection.find_one({'_mid': v.get('_id')}, {'_id': True})
    #                         if mongo_entity:
    #                             v['_id'] = mongo_entity.get('_id')
    #                             mongo_references.append(v)
    #                     if mongo_references:
    #                         id = self.mongo_collection.update({'_id': e.get('_id')}, {'$set': {'%s.%s' % (p, p_key): mongo_references}})
    #             elif type(p_value) is list:
    #                 mongo_references = []
    #                 for v in p_value:
    #                     mongo_entity = self.mongo_collection.find_one({'_mid': v.get('_id')}, {'_id': True})
    #                     if mongo_entity:
    #                         v['_id'] = mongo_entity.get('_id')
    #                         mongo_references.append(v)
    #                 if mongo_references:
    #                     id = self.mongo_collection.update({'_id': e.get('_id')}, {'$set': {p: mongo_references}})
    #             else:
    #                 mongo_entity = self.mongo_collection.find_one({'_mid': p_value.get('_id')}, {'_id': True})
    #                 if mongo_entity:
    #                     p_value['_id'] = mongo_entity.get('_id')
    #                     id = self.mongo_collection.update({'_id': e.get('_id')}, {'$set': {p: p_value}})
    #
    #         self.mongo_collection.update({'_id': e.get('_id')}, {'$unset': {'_reference_property': 1}})



    # def __get_mongodb_parent(self, entity_id, recursive=False, created=None):
    #     if created:
    #         query = self.db.query("""
    #             SELECT entity_id
    #             FROM relationship
    #             WHERE relationship_definition_keyname = 'child'
    #             AND is_deleted = 0
    #             AND entity_id IS NOT NULL
    #             AND related_entity_id = %s
    #             AND (created IS NULL OR created <= %s)
    #             AND (deleted IS NULL OR deleted > %s);
    #         """, entity_id, created, created)
    #     else:
    #         query = self.db.query("""
    #             SELECT entity_id
    #             FROM relationship
    #             WHERE relationship_definition_keyname = 'child'
    #             AND is_deleted = 0
    #             AND entity_id IS NOT NULL
    #             AND related_entity_id = %s;
    #         """, entity_id)
    #
    #     entities = []
    #     for r in query:
    #         entities.append(r.get('entity_id'))
    #         if recursive:
    #             entities = entities + self.__get_mongodb_parent(entity_id=r.get('entity_id'), recursive=True, created=created)
    #
    #     return entities


    # def __get_mongodb_right(self, entity_id, rights, created=None):
    #     sql = """
    #         SELECT related_entity_id
    #         FROM relationship
    #         WHERE relationship_definition_keyname IN (%s)
    #         AND is_deleted = 0
    #         AND related_entity_id IS NOT NULL
    #         AND entity_id = %s
    #     """ % (', '.join(['\'%s\'' % x for x in rights]), entity_id)
    #
    #     entities = []
    #     for r in self.db.query(sql):
    #         entities.append(r.get('related_entity_id'))
    #
    #     return entities



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
