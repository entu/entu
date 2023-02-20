from tornado import auth, web, httpclient
from StringIO import StringIO
from operator import itemgetter
import os
import logging
import mimetypes
import zipfile
import yaml
import json
import time

from main.helper import *
from main.db import *


class TestBug(myRequestHandler, Entity):
    def get(self):
         1 / 0

class ShowGroup(myRequestHandler, Entity):
    """
    """
    @web.removeslash
    @web.authenticated
    def get(self, entity_definition_keyname=None):
        """
        Show entities page with menu.

        """
        entity_definition_keyname = entity_definition_keyname.strip('/').split('/')[0]

        entity_definition = None
        quota_entities_used = 0
        quota_size_used = 0
        add_definitions = {}

        if entity_definition_keyname:
            entity_definition = self.get_entity_definition(entity_definition_keyname=entity_definition_keyname)
            for ad in self.get_definitions_with_optional_parent(entity_definition_keyname):
                add_definitions.setdefault(ad.get('related_entity_label'), []).append(ad)
        else:
            quota_entities_used = self.db_get('SELECT COUNT(*) AS entities FROM entity WHERE is_deleted = 0;').get('entities', 0)
            quota_size_used = self.db_get('SELECT SUM(filesize) AS size FROM file;').get('size', 0)

        self.render('entity/template/start.html',
            page_title = entity_definition[0]['label_plural'] if entity_definition else '',
            menu = self.get_menu(),
            show_list = True if entity_definition_keyname else False,
            entity_definition_label = entity_definition[0]['label_plural'] if entity_definition else '',
            entity_definition_keyname = entity_definition_keyname,
            add_definitions = add_definitions,
            quota_entities_used = int(quota_entities_used),
            quota_size = float(self.app_settings('quota-data', 0))*1000000000.0,
            quota_size_human = GetHumanReadableBytes(float(self.app_settings('quota-data', 0))*1000000000.0, 1),
            quota_size_used = int(quota_size_used) if quota_size_used else 0,
            quota_size_used_human = GetHumanReadableBytes(quota_size_used, 1) if quota_size_used else '0B'
        )


class ShowTableView(myRequestHandler, Entity):
    @web.authenticated
    def post(self, entity_definition_keyname=None):
        search = self.get_argument('q', None, True)
        limit = self.app_settings('tablepagesize', 101)
        entities = self.get_entities(search=search, entity_definition_keyname=entity_definition_keyname, full_definition=True, limit=limit)

        self.render('entity/template/table.html',
            entities = entities,
        )


class GetEntities(myRequestHandler, Entity):
    """
    """
    @web.authenticated
    def get(self):
        """
        """
        search = self.get_argument('q', None, True)
        entity_definition_keynames = StrToList(self.get_argument('definition', '', True))
        exclude_entity_id = self.get_argument('exclude_entity', '0', True)
        if not search:
            return self.missing()


        result = []
        for e in self.get_entities(search=search, entity_definition_keyname=entity_definition_keynames, limit=303):
            if exclude_entity_id:
                if e['id'] in [int(x) for x in exclude_entity_id.split(',')]:
                    continue
            result.append({
                'id':    e['id'],
                'title': e['displayname'],
                'info':  e['displayinfo'],
                'image': e['displaypicture'],
                'definition': e['label']
            })

        self.write({'entities': result})


class GetUsers(myRequestHandler, Entity):
    """
    To return list of entities that have
    'entu-user' or 'entu-api-key' property.
    """
    @web.authenticated
    def get(self):
        """
        """
        search = self.get_argument('q', None, True)
        exclude_entity_id = self.get_argument('exclude_entity', '0', True)
        if not search:
            return self.missing()


        result = []
        for e in self.get_users(search=search):
            if exclude_entity_id:
                if e['id'] in [int(x) for x in exclude_entity_id.split(',')]:
                    continue
            result.append({
                'id':    e['id'],
                'title': e['displayname'],
                'info':  e['displayinfo'],
                'image': e['displaypicture'],
                'definition': e['label']
            })

        self.write({'entities': result})


class ShowEntity(myRequestHandler, Entity):
    @web.authenticated
    def get(self, entity_id=None, url=None):
        """
        Shows Entitiy info.

        """

        if not entity_id:
            return self.missing()

        item = self.get_entities(entity_id=entity_id, limit=1)

        if not item:
            return self.missing()

        if self.request.headers.get('X-Requested-With', '').lower() != 'xmlhttprequest':
            self.redirect('/entity/%s/%s' % (item.get('definition_keyname'), entity_id))

        parents = self.get_relatives(related_entity_id=item['id'], relationship_definition_keyname='child', reverse_relation=True)
        allowed_childs = self.get_allowed_childs(entity_id=item['id'])
        allowed_parents = self.get_allowed_parents(entity_id=item['id'])

        add_definitions = {}
        for ad in self.get_definitions_with_optional_parent(item.get('definition_keyname')):
            add_definitions.setdefault(ad.get('related_entity_label'), []).append(ad)

        add_relations = {}
        for ar in self.get_definitions_with_optional_relative(item.get('definition_keyname')):
            add_relations.setdefault(ar.get('related_entity_label'), []).append(ar)

        self.render('entity/template/item.html',
            page_title = item['displayname'],
            entity = item,
            parents = parents.values() if parents else [],
            allowed_childs = allowed_childs,
            allowed_parents = allowed_parents,
            add_definitions = add_definitions,
            add_relations = add_relations,
            public_path = self.get_public_path(entity_id),
        )


class ShowEntityEdit(myRequestHandler, Entity):
    @web.authenticated
    def get(self, entity_id=None):
        """
        Shows Entitiy edit form.

        """
        item = self.get_entities(entity_id=entity_id, limit=1, full_definition=True)
        if not item:
            return

        try:
            AWS_BUCKET     = self.app_settings('auth-s3', '\n', True).split('\n')[0]
            AWS_ACCESS_KEY = self.app_settings('auth-s3', '\n', True).split('\n')[1]
            AWS_SECRET_KEY = self.app_settings('auth-s3', '\n', True).split('\n')[2]
            s3upload = True
        except Exception, e:
            s3upload = False

        self.render('entity/template/edit.html',
            entity = item,
            parent_entity_id = '',
            entity_definition_keyname = '',
            actions = ['default'],
            open_after_add = False,
            s3upload = s3upload
        )


class ShowEntityAdd(myRequestHandler, Entity):
    @web.authenticated
    def get(self, entity_id=None, entity_definition_keyname=None):
        """
        Shows Entitiy adding form.

        """
        item = self.get_entities(entity_id=0, entity_definition_keyname=entity_definition_keyname, limit=1, full_definition=True)
        if not item:
            return

        entity_definition = self.get_entity_definition(entity_definition_keyname=entity_definition_keyname)
        actions = StrToList(entity_definition[0].get('actions_add'))
        if 'default' not in actions and '-default' not in actions:
            actions.append('default')
        if '-default' in actions:
            actions.remove('-default')

        try:
            AWS_BUCKET     = self.app_settings('auth-s3', '\n', True).split('\n')[0]
            AWS_ACCESS_KEY = self.app_settings('auth-s3', '\n', True).split('\n')[1]
            AWS_SECRET_KEY = self.app_settings('auth-s3', '\n', True).split('\n')[2]
            s3upload = True
        except Exception, e:
            s3upload = False

        self.render('entity/template/edit.html',
            entity = item,
            parent_entity_id = entity_id,
            entity_definition_keyname = entity_definition_keyname,
            actions = actions,
            open_after_add = True if entity_definition[0].get('open_after_add', 0) == 1 else False,
            s3upload = s3upload
        )


class ShowEntityRelate(myRequestHandler, Entity):
    @web.authenticated
    def get(self, entity_id=None):
        """
        Shows Entitiy relate form.

        """
        item = self.get_entities(entity_id=entity_id, limit=1, full_definition=True)
        if not item:
            return

        self.render('entity/template/edit.html',
            entity = item,
            parent_entity_id = '',
            entity_definition_keyname = '',
        )


class SaveEntity(myRequestHandler, Entity):
    entity_id                   = None
    new_property_id             = None
    property_definition_keyname = None
    is_file                     = False
    value                       = None
    external_files              = {}

    @web.authenticated
    @web.asynchronous
    def post(self):
        """
        Saves Entitiy info.

        """
        if self.get_argument('is_file', default='false', strip=True).lower() == 'true':
            self.is_file                    = True
            self.value                      = self.request.files.get('value', []) if self.request.files.get('value', None) else None
        else:
            self.is_file                    = False
            self.value                      = self.get_argument('value', default=None, strip=True)
        self.entity_id                      = self.get_argument('entity_id', default=None, strip=True)
        self.new_property_id                = self.get_argument('value_id', default=None, strip=True)
        self.property_definition_keyname    = self.get_argument('property_definition_keyname', default=None, strip=True)
        parent_entity_id                    = self.get_argument('parent_entity_id', default=None, strip=True)
        entity_definition_keyname           = self.get_argument('entity_definition_keyname', default=None, strip=True)
        property_id                         = self.get_argument('value_id', default=None, strip=True)
        is_counter                          = self.get_argument('counter', default='false', strip=True)
        is_public                           = self.get_argument('is_public', default='false', strip=True)
        self.external_files                 = json.loads(self.get_argument('external_files', None)) if self.get_argument('external_files', None) else None
        external_download                   = True if self.get_argument('external_download', default='false', strip=True).lower() == 'true' else False

        if not self.entity_id and parent_entity_id and entity_definition_keyname:
            self.entity_id = self.create_entity(entity_definition_keyname=entity_definition_keyname, parent_entity_id=parent_entity_id)

        if is_counter.lower() == 'true':
            self.value = self.set_counter(entity_id=self.entity_id)
        elif is_public.lower() == 'true':
            self.value = True if self.value.lower() == 'true' else False
            self.value = self.set_public(entity_id=self.entity_id, is_public=self.value)
        elif self.external_files:
            self.value = []
            for link, filename in self.external_files.iteritems():
                self.value.append(filename)
                if external_download:
                    httpclient.AsyncHTTPClient().fetch(link, method='GET', request_timeout=3600, callback=self._got_external_file)
                else:
                    self.new_property_id = self.set_property(entity_id=self.entity_id, property_definition_keyname=self.property_definition_keyname, value={'filename': filename, 'url': link})
            if external_download:
                return
        else:
            if type(self.value) is not list:
                self.value = [self.value]
            for v in self.value:
                self.new_property_id = self.set_property(entity_id=self.entity_id, property_definition_keyname=self.property_definition_keyname, value=v, old_property_id=property_id)
            if self.is_file:
                self.value = [x['filename'] for x in self.value]
        self._printout()

    @web.asynchronous
    def _got_external_file(self, response):
        filename = self.external_files[response.request.url]
        self.new_property_id = self.set_property(entity_id=self.entity_id, property_definition_keyname=self.property_definition_keyname, value={'filename': filename, 'body': response.body})
        del self.external_files[response.request.url]
        if not self.external_files:
            self._printout()

    @web.asynchronous
    def _printout(self):
        self.write(json.dumps({
            'entity_id': self.entity_id,
            'property_definition_keyname': self.property_definition_keyname,
            'value_id': self.new_property_id,
            'value': self.value if not self.is_file else None,
            'files': self.value if self.is_file else None,
        }))
        self.finish()


class DeleteFile(myRequestHandler, Entity):
    @web.authenticated
    def post(self, file_id=None):
        """
        Delete file.

        Mandatory arguments:
        - property_id
        - entity_id

        Find entity by id and change file property (by id) to None.

        """
        property_id = self.get_argument('property_id', None, True)
        entity_id = self.get_argument('entity_id', None, True)

        item = self.get_entities(entity_id=entity_id, limit=1)
        if not item:
            return self.missing()

        self.set_property(entity_id=entity_id, old_property_id=property_id)
        self.write({'response': 'OK'})


class DeleteEntity(myRequestHandler, Entity):
    @web.authenticated
    def post(self, id=None):
        """
        Delete whole entity.
        Also recursively delete its childs

        Mandatory arguments:
        - entity_id

        1. Find childs by parent entity id and call DeleteEntity on them
        2. Mark entity's deleted property to current time and deleted_by to current user's id.

        """
        entity_id = self.get_argument('entity_id', None, True)

        item = self.get_entities(entity_id=entity_id, limit=1)
        if not item:
            return self.missing()

        self.delete_entity(entity_id)
        self.write({'response': 'OK'})


class ShareByEmail(myRequestHandler, Entity):
    @web.authenticated
    def get(self, entity_id=None):
        """
        Shows Entitiy share by email form.

        """
        self.render('entity/template/email.html',
            entity_id = entity_id,
            email = self.get_argument('email', '')
        )


class EntityRights(myRequestHandler, Entity):
    @web.authenticated
    def get(self, entity_id=None):
        """
        Shows Entitiy rights form.

        """
        rights = []
        for right, entities in self.get_rights(entity_id=entity_id).iteritems():
            for e in entities:
                rights.append({
                    'right': right,
                    'id': e.get('id'),
                    'name': e.get('displayname'),
                })

        entity = self.get_entities(entity_id=entity_id, limit=1)

        rights.append({
            'right': 'viewer',
            'id': None,
            'name': 'XXXX',
        })

        self.render('entity/template/rights.html',
            entity_id = entity_id,
            sharing = entity.get('sharing'),
            sharing_link = 'https://%s/shared/%s/%s' % (self.request.host, entity_id, entity.get('sharing_key')) if entity.get('sharing_key') else None,
            rights = sorted(rights, key=itemgetter('name')),
        )

    @web.authenticated
    def post(self, entity_id=None):

        sharing = self.get_argument('sharing', None)
        related_entity_id = self.get_argument('person', None)
        right = self.get_argument('right', None)

        if entity_id and sharing:
            self.set_sharing(entity_id=entity_id, sharing=sharing)

        elif entity_id and self.get_argument('generate_link', None):
            sharing_key = self.set_sharing_key(entity_id=entity_id, generate=True)
            self.write('https://%s/shared/%s/%s' % (self.request.host, entity_id, sharing_key))

        elif entity_id and self.get_argument('delete_link', None):
            self.set_sharing_key(entity_id=entity_id, generate=False)
            self.write('OK')

        elif entity_id and related_entity_id:
            self.set_rights(entity_id=entity_id, related_entity_id=related_entity_id, right=right)


class EntityParents(myRequestHandler, Entity):
    @web.authenticated
    def get(self, entity_id=None):
        """
        Shows Entitiy rights form.

        """

        parents = self.get_relatives(related_entity_id=entity_id, relationship_definition_keyname='child', reverse_relation=True)
        allowed_parents = self.get_allowed_parents(entity_id=entity_id)

        self.render('entity/template/parents.html',
            entity_id = entity_id,
            parents = parents.values() if parents else None,
            allowed_parents = allowed_parents,
        )

    @web.authenticated
    def post(self, entity_id=None):
        parent = self.get_argument('parent', None)
        delete = True if self.get_argument('delete', 'false', True).lower() == 'true' else False

        if not entity_id or not parent:
            return

        self.set_parent(entity_id=entity_id, parent=parent, delete=delete)

        self.write('OK')


class EntityDuplicate(myRequestHandler, Entity):
    @web.authenticated
    def get(self, entity_id=None):
        """
        Shows Entitiy duplication form.

        """

        entity = self.get_entities(entity_id=entity_id, limit=1)

        self.render('entity/template/duplicate.html',
            entity = entity,
        )

    @web.authenticated
    def post(self, entity_id=None):
        copies = self.get_argument('count', None, True)
        skip_property_definition_keyname = self.get_arguments('properties[]', True)

        if not entity_id or not copies:
            return

        self.duplicate_entity(entity_id=entity_id, copies=copies, skip_property_definition_keyname=skip_property_definition_keyname)

        self.write('OK')


class ShowHTMLproperty(myRequestHandler, Entity):
    @web.authenticated
    def get(self, entity_id, dataproperty):
        """
        Shows HTML property in modal box

        """

        item = self.get_entities(entity_id=entity_id, limit=1, full_definition=False)
        if not item:
            return

        self.write('\n'.join([x.get('value', '') for x in item.get('properties', {}).get(dataproperty, {}).get('values') if x.get('value', '')]))


handlers = [
    ('/test', TestBug),
    ('/entity/save', SaveEntity),
    ('/entity/delete-file', DeleteFile),
    ('/entity/delete-entity', DeleteEntity),
    ('/entity/search', GetEntities),
    ('/entity/users', GetUsers),
    (r'/entity/table/(.*)', ShowTableView),
    (r'/entity-(.*)/edit', ShowEntityEdit),
    (r'/entity-(.*)/relate', ShowEntityRelate),
    (r'/entity-(.*)/add/(.*)', ShowEntityAdd),
    (r'/entity-(.*)/share', ShareByEmail),
    (r'/entity-(.*)/rights', EntityRights),
    (r'/entity-(.*)/parents', EntityParents),
    (r'/entity-(.*)/duplicate', EntityDuplicate),
    (r'/entity-(.*)/html-(.*)', ShowHTMLproperty),
    (r'/entity-(.*)', ShowEntity),
    (r'/entity(.*)', ShowGroup),
]
