from tornado import auth, web

from operator import itemgetter

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
        self.render('entity/start.html',
            page_title = self.locale.translate('search_results'),
            menu = db.Entity(only_public=False, user_id=self.current_user.id).get_menu(),
            show_list = True if entity_definition_id else False
        )

    @web.authenticated
    def post(self, entity_definition_id=None):
        """
        Returns searched Entitiy IDs as JSON.

        """
        search = self.get_argument('search', None, True)
        self.write({'items': db.Entity(only_public=False, user_id=self.current_user.id).get(ids_only=True, search=search, entity_definition=entity_definition_id)})


class ShowListinfo(myRequestHandler):
    """
    """
    @web.authenticated
    def post(self, entity_id=None):
        """
        Returns Entitiy info for list as JSON.

        """
        item = db.Entity(only_public=False, user_id=self.current_user.id).get(entity_id=entity_id, limit=1)[0]
        name = ', '.join([x['value'] for x in item.setdefault('properties', {}).setdefault('title', {}).setdefault('values', {}).values()])
        self.write({
            'id': item['id'],
            'title': name,
            'image': db.Entity().get_picture_url(item['id']),
        })


class ShowEntity(myRequestHandler):
    @web.authenticated
    def get(self, id=None, url=None):
        """
        Shows Entitiy info.

        """
        item = db.Entity(only_public=True, user_id=self.current_user.id).get(id=id, limit=1)
        if not item:
            self.redirect('/public')

        item = item[0]
        item_name = ', '.join([x['value'] for x in item.setdefault('properties', {}).setdefault('title', {}).setdefault('values', {}).values()])

        props = []
        for p in item.setdefault('properties', {}).values():
            if p.setdefault('dataproperty', '') == 'title':
                continue
            if p.setdefault('datatype', '') == 'blobstore':
                value = '<br />'.join(['<a href="/public/file/%s/%s" title="%s">%s</a>' % (x['file_id'], toURL(x['value']), x['filesize'], x['value']) for x in p.setdefault('values', {}).values() if x['value']])
            else:
                value = '<br />'.join([x['value'] for x in p.setdefault('values', {}).values() if x['value']])

            props.append({
                'ordinal' : p.setdefault('ordinal', 0),
                'label' : p.setdefault('label', ''),
                'value': value
            })

        self.render('entity/item.html',
            page_title = item_name,
            item_name = item_name,
            properties = sorted(props, key=itemgetter('ordinal')),
            search = ''
        )


handlers = [
    (r'/', ShowGroup),
    (r'/group-(.*)', ShowGroup),
    (r'/entity-(.*)/listinfo', ShowListinfo),
]
