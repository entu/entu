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
import markdown2

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
        history = ''

        if entity_definition_keyname:
            entity_definition = self.get_entity_definition(entity_definition_keyname=entity_definition_keyname)
            for ad in self.get_definitions_with_optional_parent(entity_definition_keyname):
                add_definitions.setdefault(ad.get('related_entity_label'), []).append(ad)
        else:
            quota_entities_used = self.db.get('SELECT COUNT(*) AS entities FROM entity WHERE is_deleted = 0;').entities
            quota_size_used = self.db.get('SELECT SUM(filesize) AS size FROM file;').size
            try:
                f = open(os.path.join(os.path.dirname(__file__), '..', '..', 'HISTORY.md'), 'r')
                history = markdown2.markdown('## '.join(f.read().split('## ')[:4]).replace('## ', '#### '))
            except Exception, e:
                logging.error(e)
                history = ''


        self.render('entity/template/start.html',
            page_title = entity_definition[0]['label_plural'] if entity_definition else '',
            menu = self.get_menu(),
            show_list = True if entity_definition_keyname else False,
            entity_definition_label = entity_definition[0]['label_plural'] if entity_definition else '',
            entity_definition_keyname = entity_definition_keyname,
            add_definitions = add_definitions,
            history = history,
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

        self.render('entity/template/item.html',
            page_title = item['displayname'],
            entity = item,
            parents = parents.values() if parents else [],
            allowed_childs = allowed_childs,
            allowed_parents = allowed_parents,
            add_definitions = add_definitions,
            public_path = self.get_public_path(entity_id),
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
            sf = StringIO()
            zf = zipfile.ZipFile(sf, 'w', zipfile.ZIP_DEFLATED)
            links = []
            for f in files:
                if f.get('file'):
                    if f.get('url'):
                        links.append('<a href="%s" target="_blank">%s</a>' % (f.get('url'), f.get('filename').encode('utf-8')))
                    else:
                        zf.writestr('files/%s' % f.get('filename'), f.get('file'))
                        links.append('<a href="%s" target="_blank">%s</a>' % ('files/%s' % f.get('filename').encode('utf-8'), f.get('filename').encode('utf-8')))
            if links:
                linksfile = '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<style type="text/css">body {margin:50px 100px; font-family:sans-serif; font-size:13px;} a {display: block; margin-top:10px;}</style>\n</head>\n<body>\n%s\n</body>\n</html>' % '\n'.join(links)
                zf.writestr('index.html', linksfile)
            zf.close()
            mime = 'application/octet-stream'
            filename = '%s.zip' % file_ids
            outfile = sf.getvalue()
        else:
            f = files[0]
            if not f.get('file') and not f.get('url'):
                return self.missing()
            if f.get('url'):
                return self.redirect(f.get('url'))

            mimetypes.init()
            mime = mimetypes.types_map.get('.%s' % f.get('filename').lower().split('.')[-1], 'application/octet-stream')

            filename = f.get('filename')
            outfile = f.get('file')

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
                    httpclient.AsyncHTTPClient().fetch(link, method = 'GET', request_timeout = 3600, callback=self._got_external_file)
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
            entity_id = entity_id
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
            sharing_link = '%s://%s/shared/%s/%s' % (self.request.protocol, self.request.host, entity_id, entity.get('sharing_key')) if entity.get('sharing_key') else None,
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
            self.write('%s://%s/shared/%s/%s' % (self.request.protocol, self.request.host, entity_id, sharing_key))

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

        self.set_relations(entity_id=parent, related_entity_id=entity_id, relationship_definition_keyname='child', delete=delete)

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
                        'name': f.get('filename'),
                        'date': f.get('created').timetuple() if f.get('created') else time.localtime(time.time()),
                        'file': f.get('file')
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
    ('/test', TestBug),
    ('/entity/save', SaveEntity),
    ('/entity/delete-file', DeleteFile),
    ('/entity/delete-entity', DeleteEntity),
    ('/entity/search', GetEntities),
    ('/entity/users', GetUsers),
    (r'/entity/table/(.*)', ShowTableView),
    (r'/entity/file-(.*)', DownloadFile),
    (r'/entity-(.*)/edit', ShowEntityEdit),
    (r'/entity-(.*)/relate', ShowEntityRelate),
    (r'/entity-(.*)/add/(.*)', ShowEntityAdd),
    (r'/entity-(.*)/share', ShareByEmail),
    (r'/entity-(.*)/rights', EntityRights),
    (r'/entity-(.*)/parents', EntityParents),
    (r'/entity-(.*)/duplicate', EntityDuplicate),
    (r'/entity-(.*)/html-(.*)', ShowHTMLproperty),
    (r'/entity-(.*)/download', DownloadEntity),
    (r'/entity-(.*)', ShowEntity),
    (r'/entity(.*)', ShowGroup),
]
