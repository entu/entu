from tornado import auth, web

import logging

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
            page_title = entity.get_entity_definition(entity_definition_id=entity_definition_id).label_plural if entity_definition_id else '',
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
        self.write({'items': db.Entity(user_locale=self.get_user_locale(), user_id=self.current_user.id).get(ids_only=True, search=search, entity_definition=entity_definition_id, limit=1001)})


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

        relatives = entity.get_relatives(entity_id=item['id'], relation_type='child')
        allowed_childs = entity.get_allowed_childs(entity_id=item['id'])

        self.render('entity/item.html',
            page_title = item['displayname'],
            entity = item,
            relatives = relatives,
            allowed_childs = allowed_childs,
        )


class ShowEntityEdit(myRequestHandler):
    @web.authenticated
    def get(self, entity_id=None, url=None):
        """
        Shows Entitiy info.

        """
        entity = db.Entity(user_locale=self.get_user_locale(), user_id=self.current_user.id)
        item = entity.get(entity_id=entity_id, limit=1, full_definition=True)
        if not item:
            return

        self.render('entity/edit.html',
            entity = item,
        )


handlers = [
    (r'/', ShowGroup),
    (r'/group-(.*)', ShowGroup),
    (r'/entity-(.*)/listinfo', ShowListinfo),
    (r'/entity-(.*)/edit', ShowEntityEdit),
    (r'/entity-(.*)', ShowEntity),
]
