import hmac
import json
import datetime
import logging
import mimetypes
from hashlib import sha1
from operator import itemgetter

from boto.s3.connection import S3Connection
from boto.s3.key import Key


from main.helper import *
from main.db import *
from main.db2 import *




class API2EntityList(myRequestHandler, Entity2):
    @web.removeslash
    def get(self):
        #
        # Get entity list
        #
        db_result = self.get_entities_info(
                definition=self.get_argument('definition', default=None, strip=True),
                query=self.get_argument('query', default=None, strip=True),
                limit=self.get_argument('limit', default=None, strip=True),
                page=self.get_argument('page', default=None, strip=True)
            )

        result = {}
        for e in db_result.get('entities', []):
            result.setdefault(e.get('id'), {}).setdefault('definition', {})['definition'] = e.get('definition') if e.get('definition') else None
            result.setdefault(e.get('id'), {}).setdefault('definition', {})['label'] = e.get('label') if e.get('label') else None
            result.setdefault(e.get('id'), {}).setdefault('definition', {})['label_plural'] = e.get('label_plural') if e.get('label_plural') else None
            result.setdefault(e.get('id'), {}).setdefault('definition', {})['table_header'] = e.get('displaytableheader').split('|') if e.get('displaytableheader') else None
            result.setdefault(e.get('id'), {})['id'] = e.get('id') if e.get('id') else None
            result.setdefault(e.get('id'), {})['sort'] = e.get('sort') if e.get('sort') else None
            result.setdefault(e.get('id'), {})['name'] = e.get('displayname') if e.get('displayname') else None
            result.setdefault(e.get('id'), {})['info'] = e.get('displayinfo') if e.get('displayinfo') else None
            result.setdefault(e.get('id'), {})['table'] = e.get('displaytable').split('|') if e.get('displaytable') else None

        self.json({
            'result': sorted(result.values(), key=itemgetter('sort')),
            'time': round(self.request.request_time(), 3),
            'count': db_result.get('count', 0),
        })




class API2Entity(myRequestHandler, Entity):
    @web.removeslash
    def get(self, entity_id=None):
        #
        # Get entity (with given ID)
        #
        if not entity_id:
            return self.json({
                'error': 'No entity ID!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        entity = self.get_entities(entity_id=entity_id, limit=1)
        if not entity:
            return self.json({
                'error': 'Entity with given ID is not found!',
                'time': round(self.request.request_time(), 3),
            }, 404)
        entity['definition'] = {'keyname': entity['definition_keyname']}
        self.json({
            'result': entity,
            'time': round(self.request.request_time(), 3),
        })


    @web.removeslash
    def put(self, entity_id=None):
        #
        # Change entity (with given ID) properties
        #
        if not self.current_user:
            return self.json({
                'error': 'Forbidden!',
                'time': round(self.request.request_time(), 3),
            }, 403)

        if not entity_id:
            return self.json({
                'error': 'No entity ID!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        # entity = self.get_entities(entity_id=entity_id, limit=1)
        # if not entity:
        #     return self.json({
        #         'error': 'Entity with given ID is not found!',
        #         'time': round(self.request.request_time(), 3),
        #     }, 404)

        for dataproperty, value in self.request.arguments.iteritems():
            if dataproperty in ['user', 'policy', 'signature']:
                continue
            if type(value) is not list:
                value = [value]
            for v in value:
                new_property_id = self.set_property(entity_id=entity_id, property_definition_keyname=dataproperty, value=v)

        self.json({
            'entity_id': entity_id,
            'time': round(self.request.request_time(), 3),
        }, 201)


    @web.removeslash
    def post(self, entity_id=None):
        #
        # Create new child entity (under entity with given ID)
        #
        if not self.current_user:
            return self.json({
                'error': 'Forbidden!',
                'time': round(self.request.request_time(), 3),
            }, 403)

        if not entity_id:
            return self.json({
                'error': 'No entity ID!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        entity = self.get_entities(entity_id=entity_id, limit=1)
        if not entity:
            return self.json({
                'error': 'Entity with given ID is not found!',
                'time': round(self.request.request_time(), 3),
            }, 404)

        definition = self.get_argument('definition', default=None, strip=True)
        if not definition:
            return self.json({
                'error': 'No definition!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        entity_id = self.create_entity(entity_definition_keyname=definition, parent_entity_id=entity_id)

        for dataproperty, value in self.request.arguments.iteritems():
            if dataproperty in ['user', 'policy', 'signature', 'definition']:
                continue
            if type(value) is not list:
                value = [value]
            for v in value:
                new_property_id = self.set_property(entity_id=entity_id, property_definition_keyname=dataproperty, value=v)

        self.json({
            'entity_id': entity_id,
            'time': round(self.request.request_time(), 3),
        }, 201)


    @web.removeslash
    def delete(self, entity_id=None):
        #
        # Delete entity (with given ID)
        #
        pass




class API2EntityChilds(myRequestHandler, Entity2):
    @web.removeslash
    def get(self, entity_id=None):
        if not entity_id:
            return self.json({
                'error': 'No entity ID!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        db_result = self.get_entities_info(parent_entity_id=entity_id)

        result = {}
        for e in db_result.get('entities', []):
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

        self.json({
            'result': result.values(),
            'time': round(self.request.request_time(), 3),
            'count': db_result.get('count', 0),
        })




class API2EntityReferrals(myRequestHandler, Entity2):
    @web.removeslash
    def get(self, entity_id=None):
        if not entity_id:
            return self.json({
                'error': 'No entity ID!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        db_result = self.get_entities_info(referred_to_entity_id=entity_id)

        result = {}
        for e in db_result.get('entities', []):
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

        self.json({
            'result': result.values(),
            'time': round(self.request.request_time(), 3),
            'count': db_result.get('count', 0),
        })




class API2File(myRequestHandler, Entity):
    @web.removeslash
    def get(self, file_id=None):
        #
        # Get file (with given ID)
        #
        if not file_id:
            return self.json({
                'error': 'No file ID!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        files = self.get_file(file_id)
        if not files:
            return self.json({
                'error': 'File with given ID is not found!',
                'time': round(self.request.request_time(), 3),
            }, 404)

        if not files[0].file:
            return self.json({
                'error': 'No file!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        if files[0].is_link == 1:
            return self.redirect(files[0].file)

        mimetypes.init()
        mime = mimetypes.types_map.get('.%s' % files[0].filename.lower().split('.')[-1], 'application/octet-stream')

        filename = files[0].filename

        self.add_header('Content-Type', mime)
        self.add_header('Content-Disposition', 'inline; filename="%s"' % filename)
        self.write(files[0].file)

    @web.removeslash
    def delete(self, file_id=None):
        #
        # Delete file (with given ID)
        #
        pass




class API2FileUpload(myRequestHandler, Entity):
    @web.removeslash
    def post(self):
        #
        # Upload/create file
        #
        if not self.current_user:
            return self.json({
                'error': 'Forbidden!',
                'time': round(self.request.request_time(), 3),
            }, 403)

        uploaded_file = self.request.body
        if not uploaded_file:
            return self.json({
                'error': 'No file!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        try:
            file_size = int(self.request.headers.get('Content-Length', 0))
        except Exception:
            return self.json({
                'error': 'Content-Length header not set!',
                'time': round(self.request.request_time(), 3),
            }, 403)

        if file_size != len(uploaded_file):
            logging.debug(len(uploaded_file))
            return self.json({
                'error': 'File not complete!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        entity_id = self.get_argument('entity', default=None, strip=True)
        if not entity_id:
            return self.json({
                'error': 'No entity ID!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        # entity = self.get_entities(entity_id=entity_id, limit=1)
        # if not entity:
        #     return self.json({
        #         'error': 'Entity with given ID is not found!',
        #         'time': round(self.request.request_time(), 3),
        #     }, 404)

        dataproperty = self.get_argument('property', default=None, strip=True)
        if not dataproperty:
            return self.json({
                'error': 'No property!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        filename = self.get_argument('filename', default=None, strip=True)
        if not filename:
            return self.json({
                'error': 'No filename!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        new_property_id = self.set_property(entity_id=entity_id, property_definition_keyname=dataproperty, value={'filename': filename, 'body': uploaded_file, 'is_link': 0})

        self.json({
            'time': round(self.request.request_time(), 3),
        })




class API2EntityPicture(myRequestHandler, Entity2):
    @web.removeslash
    def get(self, entity_id=None):
        url = self.get_entity_picture_url(entity_id)

        if not url:
            return self.missing()

        self.redirect(url)




class API2DefinitionList(myRequestHandler, Entity2):
    @web.removeslash
    def get(self):
        menu = self.get_menu()

        self.json({
            'result': menu,
            'time': round(self.request.request_time(), 3),
        })




class API2Definition(myRequestHandler, Entity2):
    @web.removeslash
    def get(self, definition_id=None):
        if not definition_id:
            return self.json({
                'error': 'No definition ID!',
                'time': round(self.request.request_time(), 3),
            }, 400)

        definitions = self.get_entity_definitions(definition_id=definition_id)
        if not definitions:
            return self.json({
                'error': 'Definition with given ID is not found!',
                'time': round(self.request.request_time(), 3),
            }, 404)

        self.json({
            'result': definitions,
            'time': round(self.request.request_time(), 3),
        })




class API2NotFound(myRequestHandler, Entity2):
    #
    # Nice error if API method not found
    #
    def get(self, url):
        self.json({
            'error': '\'%s\' not found' % url,
            'time': round(self.request.request_time(), 3),
        }, 404)

    def put(self, url):
        self.get(url)

    def post(self, url):
        self.get(url)

    def delete(self, url):
        self.get(url)










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

            self.json({
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

            self.json({
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
    (r'/api2/entity', API2EntityList),
    (r'/api2/entity-(.*)/childs', API2EntityChilds),
    (r'/api2/entity-(.*)/referrals', API2EntityReferrals),
    (r'/api2/entity-(.*)/picture', API2EntityPicture),
    (r'/api2/entity-(.*)', API2Entity),
    (r'/api2/file', API2FileUpload),
    (r'/api2/file-(.*)', API2File),
    (r'/api2/definition', API2DefinitionList),
    (r'/api2/definition-(.*)', API2Definition),
    (r'/api2/s3upload', S3FileUpload),
    (r'/api2(.*)', API2NotFound),
]
