import hmac
import json
import datetime
import logging
from hashlib import sha1
from operator import itemgetter

from boto.s3.connection import S3Connection
from boto.s3.key import Key


from main.helper import *
from main.db2 import *

def get_entity_info(language, limit):

    return entities.values()


class API2EntityChilds(myRequestHandler, Entity2):
    @web.removeslash
    @web.authenticated
    def get(self, entity_id=None):
        language = self.get_user_locale().code

        result = {}
        for e in self.get_entities_info(parent_entity_id=entity_id):
            result.setdefault(e.get('definition'), {})['definition'] = e.get('definition') if e.get('definition') else None
            result.setdefault(e.get('definition'), {})['label'] = e.get('label') if e.get('label') else None
            result.setdefault(e.get('definition'), {})['label_plural'] = e.get('label_plural') if e.get('label_plural') else None
            result.setdefault(e.get('definition'), {})['table_header'] = e.get('displaytableheader').split('|') if e.get('displaytableheader') else None
            result.setdefault(e.get('definition'), {}).setdefault('entities', {}).setdefault(e.get('id'), {})['id'] = e.get('id') if e.get('id') else None
            result.setdefault(e.get('definition'), {}).setdefault('entities', {}).setdefault(e.get('id'), {})['sort'] = e.get('sort') if e.get('sort') else None
            result.setdefault(e.get('definition'), {}).setdefault('entities', {}).setdefault(e.get('id'), {})['name'] = e.get('displayname') if e.get('displayname') else None
            result.setdefault(e.get('definition'), {}).setdefault('entities', {}).setdefault(e.get('id'), {})['info'] = e.get('displayinfo') if e.get('displayinfo') else None
            result.setdefault(e.get('definition'), {}).setdefault('entities', {}).setdefault(e.get('id'), {})['table'] = e.get('displaytable').split('|') if e.get('displaytable') else None

        for r in result.values():
            r['entities'] = sorted(r.get('entities', {}).values(), key=itemgetter('sort'))
        self.write({
            'result': result.values(),
            'time': self.request.request_time()
        })


class API2EntityReferrals(myRequestHandler, Entity2):
    @web.removeslash
    @web.authenticated
    def get(self, entity_id=None):
        language = self.get_user_locale().code

        result = {}
        for e in self.get_entities_info(referred_to_entity_id=entity_id):
            result.setdefault(e.get('definition'), {})['definition'] = e.get('definition') if e.get('definition') else None
            result.setdefault(e.get('definition'), {})['label'] = e.get('label') if e.get('label') else None
            result.setdefault(e.get('definition'), {})['label_plural'] = e.get('label_plural') if e.get('label_plural') else None
            result.setdefault(e.get('definition'), {})['table_header'] = e.get('displaytableheader').split('|') if e.get('displaytableheader') else None
            result.setdefault(e.get('definition'), {}).setdefault('entities', {}).setdefault(e.get('id'), {})['id'] = e.get('id') if e.get('id') else None
            result.setdefault(e.get('definition'), {}).setdefault('entities', {}).setdefault(e.get('id'), {})['sort'] = e.get('sort') if e.get('sort') else None
            result.setdefault(e.get('definition'), {}).setdefault('entities', {}).setdefault(e.get('id'), {})['name'] = e.get('displayname') if e.get('displayname') else None
            result.setdefault(e.get('definition'), {}).setdefault('entities', {}).setdefault(e.get('id'), {})['info'] = e.get('displayinfo') if e.get('displayinfo') else None
            result.setdefault(e.get('definition'), {}).setdefault('entities', {}).setdefault(e.get('id'), {})['table'] = e.get('displaytable').split('|') if e.get('displaytable') else None

        for r in result.values():
            r['entities'] = sorted(r.get('entities', {}).values(), key=itemgetter('sort'))
        self.write({
            'result': result.values(),
            'time': self.request.request_time()
        })


class S3FileUpload(myRequestHandler):
    def get(self, entity_id=None, property_id=None):
        AWS_BUCKET     = self.app_settings('auth-s3', '\n', True).split('\n')[0]
        AWS_ACCESS_KEY = self.app_settings('auth-s3', '\n', True).split('\n')[1]
        AWS_SECRET_KEY = self.app_settings('auth-s3', '\n', True).split('\n')[2]

        bucket = self.get_argument('bucket', None, True)
        key = self.get_argument('key', None, True)
        etag = self.get_argument('etag', None, True)
        message = self.get_argument('message', None, True)

        if bucket and key and etag:
            s3_conn = S3Connection(AWS_ACCESS_KEY, AWS_SECRET_KEY)
            s3_bucket = s3_conn.get_bucket(bucket, validate=False)
            s3_key = s3_bucket.get_key(key)
            s3_url = s3_key.generate_url(expires_in=10, query_auth=True)

            self.write({
                'bucket': bucket,
                'key': key,
                'etag': etag,
                'message': message,
                'url': s3_url,
            })
        else:
            file_type = self.get_argument('file_type', None, True)
            if not file_type:
                file_type = 'binary/octet-stream'

            key = '%s/%s' % (self.app_settings('database-name'), datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
            policy = {
                'expiration': (datetime.datetime.utcnow()+datetime.timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%SZ'),
                'conditions': [
                    {'bucket': AWS_BUCKET},
                    ['starts-with', '$key', key],
                    {'acl': 'private'},
                    {'success_action_status': '201'},
                    {'x-amz-server-side-encryption': 'AES256'},
                    {'Content-Type': file_type},
                ]
            }
            encoded_policy = json.dumps(policy).encode('utf-8').encode('base64').replace('\n','')
            signature = hmac.new(AWS_SECRET_KEY, encoded_policy, sha1).digest().encode('base64').replace('\n','')

            self.write({
                'url': 'https://%s.s3.amazonaws.com/' % AWS_BUCKET,
                'data': {
                    'key':                          '%s/${filename}' % key,
                    'acl':                          'private',
                    'success_action_status':        '201',
                    'x-amz-server-side-encryption': 'AES256',
                    'AWSAccessKeyId':               AWS_ACCESS_KEY,
                    'policy':                       encoded_policy,
                    'signature':                    signature,
                    'Content-Type':                 file_type,
                }
            })


handlers = [
    (r'/api2/entity-(.*)/childs', API2EntityChilds),
    (r'/api2/entity-(.*)/referrals', API2EntityReferrals),
    (r'/api2/s3upload', S3FileUpload),
]
