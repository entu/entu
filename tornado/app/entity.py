from tornado import auth, web

import logging
import magic

import db
from helper import *


class ShowGroup(myRequestHandler):
    """
    """
    @web.authenticated
    def get(self, entity_definition_id=None):
        """
        Show entities page with menu.

        """
        entity = db.Entity(user_locale=self.get_user_locale(), user_id=self.current_user.id)
        self.render('entity/start.html',
            page_title = entity.get_entity_definition(entity_definition_id=entity_definition_id)[0].label_plural if entity_definition_id else '',
            menu = entity.get_menu(),
            show_list = True if entity_definition_id else False,
            entity_definition = entity_definition_id,
        )

    @web.authenticated
    def post(self, entity_definition_id=None):
        """
        Returns searched Entitiy IDs as JSON.

        """
        search = self.get_argument('search', None, True)
        self.write({'items': db.Entity(user_locale=self.get_user_locale(), user_id=self.current_user.id).get(ids_only=True, search=search, entity_definition_id=entity_definition_id, limit=303)})


class ShowListinfo(myRequestHandler):
    """
    """
    @web.authenticated
    def post(self, entity_id=None):
        """
        Returns Entitiy info for list as JSON.

        """
        entity = db.Entity(user_locale=self.get_user_locale(), user_id=self.current_user.id)
        item = entity.get(entity_id=entity_id, limit=1)
        if not item:
            return self.missing()

        self.write({
            'id': item['id'],
            'title': item['displayname'],
            'info': item['displayinfo'],
            'image': item['displaypicture'],
        })


class ShowEntity(myRequestHandler):
    @web.authenticated
    def get(self, entity_id=None, url=None):
        """
        Shows Entitiy info.

        """
        entity = db.Entity(user_locale=self.get_user_locale(), user_id=self.current_user.id)
        item = entity.get(entity_id=entity_id, limit=1)

        if not item:
            return self.missing()

        relatives = entity.get_relatives(entity_id=item['id'], relation_type=['child','leecher'])
        parents = entity.get_relatives(related_entity_id=item['id'], relation_type='child', reverse_relation=True)
        allowed_childs = entity.get_allowed_childs(entity_id=item['id'])
        leecher_in = entity.get_relatives(related_entity_id=item['id'], relation_type='leecher', reverse_relation=True)

        can_edit = False if self.current_user.provider == 'application' else True #entity.get_relatives(ids_only=True, entity_id=item['id'], related_entity_id=self.current_user.id, relation_type=['viewer', 'editor', 'owner'])
        can_add = False if self.current_user.provider == 'application' else True #entity.get_relatives(ids_only=True, entity_id=item['id'], related_entity_id=self.current_user.id, relation_type=['viewer', 'editor', 'owner'])

        rating_scale = None
        # rating_scale_list = [x.get('values', []) for x in item.get('properties', []) if x.get('dataproperty', '') == 'rating_scale']
        # if rating_scale_list:
        #     rating_scale = rating_scale_list[0][0]


        self.render('entity/item.html',
            page_title = item['displayname'],
            entity = item,
            relatives = dict(leecher_in.items() + relatives.items()),
            parents = parents,
            allowed_childs = allowed_childs,
            rating_scale = rating_scale,
            can_edit = can_edit,
            can_add = can_add,
            is_owner = True,
        )


class DownloadFile(myRequestHandler):
    @web.authenticated
    def get(self, file_id=None, url=None):
        """
        Download file.

        """
        try:
            file_id = int(file_id.split('/')[0])
        except:
            return self.missing()

        file = db.Entity(user_locale=self.get_user_locale(), user_id=self.current_user.id).get_file(file_id)
        if not file:
            return self.missing()

        ms = magic.open(magic.MAGIC_MIME)
        ms.load()
        mime = ms.buffer(file.file)
        ms.close()

        self.add_header('Content-Type', mime)
        self.add_header('Content-Disposition', 'attachment; filename="%s"' % file.filename)
        self.write(file.file)



class ShowEntityEdit(myRequestHandler):
    @web.authenticated
    def get(self, entity_id=None):
        """
        Shows Entitiy edit form.

        """
        entity = db.Entity(user_locale=self.get_user_locale(), user_id=self.current_user.id)
        item = entity.get(entity_id=entity_id, limit=1, full_definition=True)
        if not item:
            return

        self.render('entity/edit.html',
            entity = item,
            parent_entity_id = '',
            entity_definition_id = '',
        )


class ShowEntityAdd(myRequestHandler):
    @web.authenticated
    def get(self, entity_id=None, entity_definition_id=None):
        """
        Shows Entitiy adding form.

        """
        entity = db.Entity(user_locale=self.get_user_locale(), user_id=self.current_user.id)
        item = entity.get(entity_id=0, entity_definition_id=entity_definition_id, limit=1, full_definition=True)
        if not item:
            return

        self.render('entity/edit.html',
            entity = item,
            parent_entity_id = entity_id,
            entity_definition_id = entity_definition_id,
        )


class ShowEntityRelate(myRequestHandler):
    @web.authenticated
    def get(self, entity_id=None):
        """
        Shows Entitiy relate form.

        """
        entity = db.Entity(user_locale=self.get_user_locale(), user_id=self.current_user.id)
        item = entity.get(entity_id=entity_id, limit=1, full_definition=True)
        if not item:
            return

        self.render('entity/edit.html',
            entity = item,
            parent_entity_id = '',
            entity_definition_id = '',
        )


class SaveEntity(myRequestHandler):
    @web.authenticated
    def post(self):
        """
        Saves Entitiy info.

        """
        entity_id               = self.get_argument('entity_id', default=None, strip=True)
        parent_entity_id        = self.get_argument('parent_entity_id', default=None, strip=True)
        entity_definition_id    = self.get_argument('entity_definition_id', default=None, strip=True)
        property_definition_id  = self.get_argument('property_id', default=None, strip=True)
        property_id             = self.get_argument('value_id', default=None, strip=True)
        value                   = self.get_argument('value', default=None, strip=True)
        is_counter              = self.get_argument('counter', default='false', strip=True)
        is_public               = self.get_argument('is_public', default='false', strip=True)
        uploaded_file           = self.request.files.get('file', [])[0] if self.request.files.get('file', None) else None

        entity = db.Entity(user_locale=self.get_user_locale(), user_id=self.current_user.id)
        if not entity_id and parent_entity_id and entity_definition_id:
            entity_id = entity.create(entity_definition_id=entity_definition_id, parent_entity_id=parent_entity_id)

        if is_counter.lower() == 'true':
            value = entity.set_counter(entity_id=entity_id)
        elif is_public.lower() == 'true':
            value = True if value.lower() == 'true' else False
            value = entity.set_public(entity_id=entity_id, is_public=value)
        else:
            property_id = entity.set_property(entity_id=entity_id, property_definition_id=property_definition_id, value=value, property_id=property_id, uploaded_file=uploaded_file)

        self.write({
            'entity_id': entity_id,
            'property_id': property_definition_id,
            'value_id': property_id,
            'value': uploaded_file['filename'] if uploaded_file else value
        })

class ShareByEmail(myRequestHandler):
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

        entity = db.Entity(user_locale=self.get_user_locale(), user_id=self.current_user.id)
        item = entity.get(entity_id=entity_id, limit=1)
        if not item:
            return self.missing()

        url = 'http://%s/entitygroup-%s#%s' % (self.request.headers.get('Host'), item['definition_id'], item['id'])

        self.mail_send(
            to = to,
            subject = item['displayname'],
            message = '%s\n\n%s\n\n%s\n%s' % (message, url, self.current_user.name, self.current_user.email)
        )

handlers = [
    (r'/entity', ShowGroup),
    (r'/entitygroup-(.*)', ShowGroup),
    (r'/entity/save', SaveEntity),
    (r'/entity/file-(.*)', DownloadFile),
    (r'/entity-(.*)/listinfo', ShowListinfo),
    (r'/entity-(.*)/edit', ShowEntityEdit),
    (r'/entity-(.*)/relate', ShowEntityRelate),
    (r'/entity-(.*)/add/(.*)', ShowEntityAdd),
    (r'/entity-(.*)/share', ShareByEmail),
    (r'/entity-(.*)', ShowEntity),
]
