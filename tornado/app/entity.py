from tornado import auth, web

from operator import itemgetter
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
        self.render('entity/start.html',
            page_title = self.locale.translate('search_results'),
            menu = db.Entity(user_locale=self.get_user_locale(), user_id=self.current_user.id).get_menu(),
            show_list = True if entity_definition_id else False
        )

    @web.authenticated
    def post(self, entity_definition_id=None):
        """
        Returns searched Entitiy IDs as JSON.

        """
        search = self.get_argument('search', None, True)
        self.write({'items': db.Entity(user_locale=self.get_user_locale(), user_id=self.current_user.id).get(ids_only=True, search=search, entity_definition=entity_definition_id)})


class ShowListinfo(myRequestHandler):
    """
    """
    @web.authenticated
    def post(self, entity_id=None):
        """
        Returns Entitiy info for list as JSON.

        """
        entity = db.Entity(user_locale=self.get_user_locale(), user_id=self.current_user.id)
        item = entity.get(entity_id=entity_id, limit=1)[0]
        name = ', '.join([x['value'] for x in sorted(item.get('properties', {}).values(), key=itemgetter('ordinal'))[0].get('values', {}).values()])
        self.write({
            'id': item['id'],
            'title': name,
            'image': entity.get_picture_url(item['id']),
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
            return

        item = item[0]
        item_name = ', '.join([x['value'] for x in item.get('properties', {}).get('title', {}).get('values', {}).values()])
        item_picture = entity.get_picture_url(entity_id=item['id'])

        relatives = entity.get_relatives(entity_id=item['id'], relation_type='subbubble')

        props = []
        for p in item.get('properties', {}).values():
            if p.get('datatype', '') == 'blobstore':
                value = '<br />'.join(['<a href="/public/file-%s/%s" title="%s">%s</a>' % (x['file_id'], toURL(x['value']), x['filesize'], x['value']) for x in p.get('values', {}).values() if x['value']])
            else:
                value = '<br />'.join(['%s' % x['value'] for x in p.get('values', {}).values() if x['value']])

            props.append({
                'ordinal' : p.get('ordinal', 0),
                'label' : p.get('label', ''),
                'value': value
            })

        self.render('entity/item.html',
            item_name = item_name,
            item_picture = item_picture,
            properties = sorted(props, key=itemgetter('ordinal')),
            relatives = relatives,
        )


handlers = [
    (r'/', ShowGroup),
    (r'/group-(.*)', ShowGroup),
    (r'/entity-(.*)/listinfo', ShowListinfo),
    (r'/entity-(.*)', ShowEntity),
]
