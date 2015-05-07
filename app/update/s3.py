import argparse
import os
import sys
import time
import torndb
import yaml
import mimetypes
import urllib

from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING
from operator import itemgetter

from boto.s3.connection import S3Connection
from boto.s3.key import Key




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




class S3files():
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

    def files(self):
        sql = """
            SELECT
                file.id,
                file.md5,
                file.s3_key,
                CONCAT('%s_2', '/', property.entity_id, '/', property.id) AS new_key,
                file.filename,
                file.filesize
            FROM file
            LEFT JOIN property ON property.value_file = file.id
            WHERE file.url IS NULL
            AND file.s3_key IS NOT NULL
            -- AND file.md5 IS NOT NULL
            ORDER BY id
            -- LIMIT 1000;
        """ % self.db_name


        s3_conn   = S3Connection(AWS_ACCESS_KEY, AWS_SECRET_KEY)
        s3_bucket = s3_conn.get_bucket(AWS_BUCKET, validate=False)

        rows = self.db.query(sql)
        for r in rows:
            s3_key = s3_bucket.get_key(r.s3_key)
            if not s3_key:
                print 'ERROR: %s - %s no S3 key' % (r.id, r.s3_key)
                continue

            if not r.filename:
                continue

            # if r.filename:
            #     mimetypes.init()
            #     mime = mimetypes.types_map.get('.%s' % r.filename.lower().split('.')[-1], 'application/octet-stream')
            # else:
            #     mime = 'application/octet-stream'

            if s3_key.content_disposition != 'inline; filename*=UTF-8\'\'%s' % urllib.quote(r.filename.encode('utf-8')):
                # if r.filename:
                #     mimetypes.init()
                #     mime = mimetypes.types_map.get('.%s' % r.filename.lower().split('.')[-1], 'application/octet-stream')
                #     metadata = {
                #         'Content-Type': mime,
                #         'Content-Disposition': 'inline; filename*=UTF-8\'\'%s' % urllib.quote(r.filename.encode('utf-8'))
                #     }
                # else:
                #     metadata = {
                #         'Content-Type': 'application/octet-stream'
                #     }

                # new_key = s3_key.copy(
                #     dst_bucket   = s3_key.bucket.name,
                #     dst_key      = s3_key.name,
                #     metadata     = metadata,
                #     encrypt_key  = True
                # )

                print 'ERROR: %s - %s - %s - %s' % (r.id, r.s3_key, r.filename, s3_key.content_disposition)
                continue


            # if r.md5:
            #     if r.md5 != s3_key.etag[1:][:-1]:
            #         print 'ERROR: %s - %s - %s' % (r.id, r.md5, s3_key.etag[1:-1])

            # if r.filesize != s3_key.size:
            #     print 'ERROR: %s - %s - %s' % (r.id, r.filesize, s3_key.size)


            # if r.new_key:
            #     print 'ERROR: %s - %s new_key' % (r.id, r.s3_key)
            #     continue

            # old_file = os.path.join('/', 'entu', 'oldfiles', r.md5[0], r.md5)
            # if not os.path.exists(old_file):

            #     s3_key = s3_bucket.get_key(self.db_name + '/' + r.md5[0] + '/' + r.md5)
            #     if s3_key:

            #         if r.filename:
            #             mimetypes.init()
            #             mime = mimetypes.types_map.get('.%s' % r.filename.lower().split('.')[-1], 'application/octet-stream')
            #             metadata = {
            #                 'Content-Type': mime,
            #                 'Content-Disposition': 'inline; filename*=UTF-8\'\'%s' % urllib.quote(r.filename.encode('utf-8'))
            #             }

            #         else:
            #             metadata = {
            #                 'Content-Type': 'application/octet-stream'
            #             }

            #         new_key = s3_key.copy(
            #             dst_bucket   = 'entu-files',
            #             dst_key      = r.new_key,
            #             metadata     = metadata,
            #             encrypt_key  = True
            #         )
            #         new_key.set_acl('private')

            #         self.db.execute('UPDATE file set s3_key = %s, changed = NOW(), changed_by = \'s3copy3\' WHERE id = %s LIMIT 1;', r.new_key, r.id)

            #         print 'ERROR: %s - %s S3 file found' % (r.id, r.s3_key)
                    # continue

                # s3_file = Key(s3_bucket)
                # s3_file.key = r.new_key
                # if r.filename:
                #     mimetypes.init()
                #     s3_file.content_type = mimetypes.types_map.get('.%s' % r.filename.lower().split('.')[-1], 'application/octet-stream')
                #     s3_file.set_metadata('Content-Disposition', 'inline; filename*=UTF-8\'\'%s' % urllib.quote(r.filename.encode('utf-8')))
                # else:
                #     s3_file.content_type = 'application/octet-stream'
                # s3_file.set_contents_from_filename(old_file, encrypt_key=True)

                # self.db.execute('UPDATE file set s3_key = %s, changed = NOW(), changed_by = \'s3copy3\' WHERE id = %s LIMIT 1;', r.new_key, r.id)

                # new_dir = os.path.join('/', 'entu', 'oldfiles', r.md5[0])
                # new_file = os.path.join(new_dir, r.md5)

                # if not os.path.exists(new_dir):
                #     os.makedirs(new_dir)
                # os.rename(old_file, new_file)

                # print 'ERROR: %s - %s - %s' % (r.id, old_file, r.new_key)


            # old_file = os.path.join('/', 'entu', 'files', self.db_name, r.md5[0], r.md5)
            # if os.path.exists(os.path.join('/', 'entu', 'files', self.db_name, r.md5[0], r.md5)):
            #     print 'ERROR: %s - %s file not in S3' % (r.id, r.s3_key)

            # if not r.new_key:
            #     print 'ERROR: %s - %s new key not set' % (r.id, r.old_key)
            #     continue

            # if r.filename:
            #     mimetypes.init()
            #     mime = mimetypes.types_map.get('.%s' % r.filename.lower().split('.')[-1], 'application/octet-stream')
            #     metadata = {
            #         'Content-Type': mime,
            #         'Content-Disposition': 'inline; filename*=UTF-8\'\'%s' % urllib.quote(r.filename.encode('utf-8'))
            #     }
            # else:
            #     metadata = {
            #         'Content-Type': 'application/octet-stream'
            #     }

            # new_key = s3_key.copy(
            #     dst_bucket   = s3_key.bucket.name,
            #     dst_key      = r.new_key,
            #     metadata     = metadata,
            #     encrypt_key  = True
            # )
            # new_key.set_acl('private')

            # if not new_key:
            #     print 'ERROR: %s - %s copy failed' % (r.id, r.s3_key)
            #     continue

            # self.db.execute('UPDATE file set s3_key = %s, changed = NOW(), changed_by = \'s3copy2\' WHERE id = %s LIMIT 1;', r.new_key, r.id)

            # s3_key2 = s3_bucket.get_key(r.new_key)
            # if not s3_key2:
            #     print 'ERROR: %s - %s new S3 file not found' % (r.id, r.s3_key)
            #     continue

            # s3_key.delete()

            # self.db.execute('UPDATE file set s3_key = %s, changed = NOW(), changed_by = \'s3copy\' WHERE id = %s LIMIT 1;', r.new_key, r.id)

            # if not self.db.get('SELECT id FROM file WHERE md5 = %s AND s3_key IS NULL LIMIT 1;', r.md5):
            #     old_file = os.path.join('/', 'entu', 'files', self.db_name, r.md5[0], r.md5)
            #     new_dir = os.path.join('/', 'entu', 'oldfiles', r.md5[0])
            #     new_file = os.path.join(new_dir, r.md5)
            #     if os.path.exists(old_file):
            #         if not os.path.exists(new_dir):
            #             os.makedirs(new_dir)
            #         os.rename(old_file, new_file)
            #     else:
            #         print 'ERROR: %s - %s file not found' % (r.id, r.old_key)

            #     s3_key.delete()

            # if args.verbose > 3: print '%s -> %s -> %s' % (r.id, r.old_key, new_key.key)


print '\n\n\n\n\n'
for c in customers():
    # if c.get('database-name') in ['okupatsioon', 'are', 'akg']:
    #     continue

    if c.get('database-name') not in ['www']:
        continue

    print '%s %s started' % (datetime.now(), c.get('database-name'))

    m2m = S3files(
        db_host = c.get('database-host'),
        db_name = c.get('database-name'),
        db_user = c.get('database-user'),
        db_pass = c.get('database-password')
    )
    m2m.files()

    print '%s %s ended' % (datetime.now(), c.get('database-name'))
    print '%s' % yaml.safe_dump(m2m.stats, default_flow_style=False, allow_unicode=True)
