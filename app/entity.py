from tornado import auth, web, httpclient
from StringIO import StringIO
from operator import itemgetter
import logging
import magic
import zipfile
import yaml
import time
import markdown2

from helper import *
from db import *


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
        if entity_definition_keyname:
            entity_definition = self.get_entity_definition(entity_definition_keyname=entity_definition_keyname)

        quota_entities_used = self.db.get('SELECT COUNT(*) AS entities FROM entity WHERE is_deleted = 0;').entities
        # quota_size_used = self.db.get('SELECT SUM(data_length + index_length) AS size FROM information_schema.TABLES;').size
        quota_size_used = self.db.get('SELECT SUM(filesize) AS size FROM file;').size

        try:
            f = open('../HISTORY.md', 'r')
            history = markdown2.markdown('## '.join(f.read().split('## ')[:4]).replace('## ', '#### '))
        except:
            history = ''

        self.render('entity/start.html',
            page_title = entity_definition[0].label_plural if entity_definition else '',
            menu = self.get_menu(),
            show_list = True if entity_definition_keyname else False,
            entity_definition_label = entity_definition[0].label_plural if entity_definition else '',
            entity_definition_keyname = entity_definition_keyname,
            add_definitions = self.get_definitions_with_default_parent(entity_definition_keyname) if entity_definition_keyname else None,
            history = history,
            quota_entities = int(self.app_settings['quota_entities']),
            quota_entities_used = int(quota_entities_used),
            quota_size = int(self.app_settings['quota_size_bytes']),
            quota_size_human = GetHumanReadableBytes(self.app_settings['quota_size_bytes'], 1),
            quota_size_used = int(quota_size_used) if quota_size_used else 0,
            quota_size_used_human = GetHumanReadableBytes(quota_size_used, 1) if quota_size_used else '0B'
        )

    @web.authenticated
    def post(self, entity_definition_keyname=None):
        """
        Returns searched Entitiy IDs as JSON.

        """
        entity_definition_keyname = entity_definition_keyname.strip('/').split('/')[0]
        search = self.get_argument('search', None, True)
        limit = 500
        self.write({
            'items': self.get_entities(ids_only=True, search=search, entity_definition_keyname=entity_definition_keyname, limit=limit+1),
            'limit': limit,
        })


class ShowListinfo(myRequestHandler, Entity):
    """
    """
    @web.authenticated
    def post(self, entity_id=None):
        """
        Returns Entitiy info for list as JSON.

        """
        item = self.get_entities(entity_id=entity_id, limit=1)
        if not item:
            return self.missing()

        self.write({
            'id': item['id'],
            'title': item['displayname'],
            'info': item['displayinfo'],
            'image': item['displaypicture'],
        })


class GetEntities(myRequestHandler, Entity):
    """
    """
    @web.authenticated
    def get(self):
        """
        """
        search = self.get_argument('q', None, True)
        entity_definition_keyname = self.get_argument('definition', None, True)
        exclude_entity_id = self.get_argument('exclude_entity', 0, True)
        if not search:
            return self.missing()


        result = []
        for e in self.get_entities(search=search, entity_definition_keyname=entity_definition_keyname, limit=303):
            if e['id'] == int(exclude_entity_id):
                continue
            result.append({
                'id':    e['id'],
                'title': e['displayname'],
                'info':  e['displayinfo'],
                'image': e['displaypicture'],
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

        relatives = self.get_relatives(entity_id=item['id'], relationship_definition_keyname=['child'])
        parents = self.get_relatives(related_entity_id=item['id'], relationship_definition_keyname='child', reverse_relation=True)
        allowed_childs = self.get_allowed_childs(entity_id=item['id'])

        can_edit = False if self.current_user.provider == 'application' else True #self.get_relatives(ids_only=True, entity_id=item['id'], related_entity_id=self.current_user.id, relationship_definition_keyname=['viewer', 'editor', 'owner'])
        can_add = False if self.current_user.provider == 'application' else True #self.get_relatives(ids_only=True, entity_id=item['id'], related_entity_id=self.current_user.id, relationship_definition_keyname=['viewer', 'editor', 'owner'])

        rating_scale = None
        # rating_scale_list = [x.get('values', []) for x in item.get('properties', []) if x.get('dataproperty', '') == 'rating_scale']
        # if rating_scale_list:
        #     rating_scale = rating_scale_list[0][0]


        self.render('entity/item.html',
            page_title = item['displayname'],
            entity = item,
            relatives = relatives,
            parents = parents.values() if parents else [],
            allowed_childs = allowed_childs,
            rating_scale = rating_scale,
            can_edit = can_edit,
            can_add = can_add,
            is_owner = True,
            add_definitions = self.get_definitions_with_default_parent(item.get('definition_keyname')) if item.get('definition_keyname') else None,
        )


class DownloadFile(myRequestHandler, Entity):
    @web.authenticated
    def get(self, file_ids=None, url=None):
        """
        Download file.

        """
        file_ids = file_ids.split('/')[0]
        files = self.get_file(file_ids)

        if not files:
            return self.missing()
        if len(files) < 1:
            return self.missing()

        if len(files) > 1:
            f = StringIO()
            zf = zipfile.ZipFile(f, 'w', zipfile.ZIP_DEFLATED)
            for file in files:
                if file.file:
                    zf.writestr(file.filename, file.file)
            zf.close()
            mime = 'application/octet-stream'
            filename = '%s.zip' % file_ids
            outfile = f.getvalue()
        else:
            file = files[0]
            if not file.file:
                return self.missing()
            ms = magic.open(magic.MAGIC_MIME)
            ms.load()
            mime = ms.buffer(file.file)
            ms.close()
            filename = file.filename
            outfile = file.file

        self.add_header('Content-Type', mime)
        self.add_header('Content-Disposition', 'inline; filename="%s"' % filename)
        self.write(outfile)


class ShowEntityEdit(myRequestHandler, Entity):
    @web.authenticated
    def get(self, entity_id=None):
        """
        Shows Entitiy edit form.

        """
        item = self.get_entities(entity_id=entity_id, limit=1, full_definition=True)
        if not item:
            return

        self.render('entity/edit.html',
            entity = item,
            parent_entity_id = '',
            entity_definition_keyname = '',
            actions = [],
            open_after_add = False,
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

        self.render('entity/edit.html',
            entity = item,
            parent_entity_id = entity_id,
            entity_definition_keyname = entity_definition_keyname,
            actions = actions,
            open_after_add = True if entity_definition[0].get('open_after_add', 0) == 1 else False,
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

        self.render('entity/edit.html',
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
        dropbox_file                        = self.get_argument('dropbox_file', default=None, strip=True)
        dropbox_name                        = self.get_argument('dropbox_name', default=None, strip=True)

        if not self.entity_id and parent_entity_id and entity_definition_keyname:
            self.entity_id = self.create(entity_definition_keyname=entity_definition_keyname, parent_entity_id=parent_entity_id)

        if is_counter.lower() == 'true':
            self.value = self.set_counter(entity_id=self.entity_id)
        elif is_public.lower() == 'true':
            self.value = True if self.value.lower() == 'true' else False
            self.value = self.set_public(entity_id=self.entity_id, is_public=self.value)
        elif dropbox_file and dropbox_name:
            self.value = [{'filename': dropbox_name, 'body': None}]
            httpclient.AsyncHTTPClient().fetch(dropbox_file, method = 'GET', request_timeout = 3600, callback=self._got_dropbox_file)
            return
        else:
            if type(self.value) is not list:
                self.value = [self.value]
            for v in self.value:
                self.new_property_id = self.set_property(entity_id=self.entity_id, property_definition_keyname=self.property_definition_keyname, value=v, old_property_id=property_id)

        self._printout()

    @web.asynchronous
    def _got_dropbox_file(self, response):
        self.value[0]['body'] = response.body
        self.new_property_id = self.set_property(entity_id=self.entity_id, property_definition_keyname=self.property_definition_keyname, value=self.value[0])
        self._printout()

    @web.asynchronous
    def _printout(self):
        self.write({
            'entity_id': self.entity_id,
            'property_definition_keyname': self.property_definition_keyname,
            'value_id': self.new_property_id,
            'value': ', '.join([x['filename'] for x in self.value]) if self.is_file else self.value
        })
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

        self.delete(entity_id)


class ShareByEmail(myRequestHandler, Entity):
    @web.authenticated
    def get(self,  entity_id=None):
        """
        Shows Entitiy share by email form.

        """
        self.render('entity/email.html',
            entity_id = entity_id
        )

    @web.authenticated
    def post(self,  entity_id=None):
        if not self.get_argument('to', None):
            return self.missing()

        to = self.get_argument('to', None)
        message = self.get_argument('message', '')

        item = self.get_entities(entity_id=entity_id, limit=1)
        if not item:
            return self.missing()

        url = 'https://%s/entity/%s/%s' % (self.request.headers.get('Host'), item['definition_keyname'], item['id'])

        self.mail_send(
            to = to,
            subject = item['displayname'],
            message = '%s\n\n%s\n\n%s\n%s' % (message, url, self.current_user.name, self.current_user.email)
        )


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


class DownloadEntity(myRequestHandler, Entity):
    @web.authenticated
    def get(self, entity_id):
        """
        Download Entity as ZIP file

        """

        item = self.get_entities(entity_id=entity_id, limit=1, full_definition=False)
        if not item:
            return

        files = self.__get_files(entity_id)

        f = StringIO()
        zf = zipfile.ZipFile(f, 'w', zipfile.ZIP_DEFLATED)
        for file in files:
            filename = '%s/%s' % (file.get('path').strip('/'), file.get('name'))
            info = zipfile.ZipInfo(filename, date_time=file.get('date'))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.create_system=0
            zf.writestr(info, file.get('file'))
        zf.close()

        self.add_header('Content-Type', 'application/octet-stream')
        self.add_header('Content-Disposition', 'inline; filename="%s.zip"' % item.get('displayname'))
        self.write(f.getvalue())


        self.write(str(files))


    def __get_files(self, entity_id, path = ''):
        """
        Return Entity properties as YAML file and all files (from file properties)

        """

        item = self.get_entities(entity_id=entity_id, limit=1, full_definition=False)
        if not item:
            return

        result = []
        path = '%s/%s #%s - %s' % (path, item.get('label').replace('/', '_'), item.get('id'), item.get('displayname').replace('/', '_'))

        itemyaml = {}
        itemyaml['created'] = str(item.get('created'))
        itemyaml['changed'] = str(item.get('changed')) if item.get('changed') else str(item.get('created'))
        for p in sorted(item.get('properties', {}).values(), key=itemgetter('ordinal')):
            for v in sorted(p.get('values', []), key=itemgetter('ordinal')):
                if v.get('value'):
                    itemyaml.setdefault('properties', {}).setdefault(p.get('dataproperty','').lower(), []).append(u'%s' % v.get('value'))

            if len(itemyaml.get('properties', {}).get(p.get('dataproperty','').lower(), [])) == 1:
                itemyaml['properties'][p.get('dataproperty','').lower()] = itemyaml.get('properties', {}).get(p.get('dataproperty','').lower(), [])[0]


            if p.get('datatype') == 'file':
                for f in self.get_file([x.get('db_value') for x in p.get('values', []) if x.get('db_value')]):
                    result.append({
                        'path': '%s/%s' % (path, p.get('label_plural', p.get('label', p.get('keyname',''))).replace('/', '_')),
                        'name': f.filename,
                        'date': f.get('created').timetuple() if f.get('created') else time.localtime(time.time()),
                        'file': f.file
                    })

        result.append({
            'path': path,
            'name': 'entity.yaml',
            'date': item.get('changed').timetuple() if item.get('changed') else time.localtime(time.time()),
            'file': yaml.safe_dump(itemyaml, default_flow_style=False, allow_unicode=True)
        })

        for definition, relatives in self.get_relatives(entity_id=entity_id, relationship_definition_keyname='child').iteritems():
            for r in relatives:
                relatives_result = self.__get_files(r.get('id'), path)
                if relatives_result:
                    result = result + relatives_result

        return result


handlers = [
    ('/entity/save', SaveEntity),
    ('/entity/delete-file', DeleteFile),
    ('/entity/delete-entity', DeleteEntity),
    ('/entity/search', GetEntities),
    (r'/entity/file-(.*)', DownloadFile),
    (r'/entity-(.*)/listinfo', ShowListinfo),
    (r'/entity-(.*)/edit', ShowEntityEdit),
    (r'/entity-(.*)/relate', ShowEntityRelate),
    (r'/entity-(.*)/add/(.*)', ShowEntityAdd),
    (r'/entity-(.*)/share', ShareByEmail),
    (r'/entity-(.*)/html-(.*)', ShowHTMLproperty),
    (r'/entity-(.*)/download', DownloadEntity),
    (r'/entity-(.*)', ShowEntity),
    (r'/entity(.*)', ShowGroup),
]
