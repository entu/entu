from tornado import auth, web

from operator import itemgetter

from helper import *
from db import *


class ShowGroup(myRequestHandler):
    @web.authenticated
    def get(self, definition_id=None):
        self.render('bubble/start.html',
            page_title = self.locale.translate('search_results'),
            menu = myDb().getMenu(user_id=self.current_user.id),
            definition_id = definition_id
        )

    @web.authenticated
    def post(self, definition_id=None):
        search = self.get_argument('search', None, True)
        self.write({'items': myDb().getBubbleIdList(search=search, only_public=False, bubble_definition=definition_id, user_id=self.current_user.id)})


class ShowBubbleListinfo(myRequestHandler):
    @web.authenticated
    def post(self, bubble_id=None):
        item = myDb().getBubbleList(bubble_id=bubble_id, only_public=False, limit=1)[0]
        name = ', '.join([x['value'] for x in item.setdefault('properties', {}).setdefault('title', {}).setdefault('values', {}).values()])
        self.write({
            'id': item['id'],
            'title': name,
            'image': myDb().getBubbleImage(item['id']),
        })


handlers = [
    (r'/', ShowGroup),
    (r'/group-(.*)', ShowGroup),
    (r'/item-(.*)/listinfo', ShowBubbleListinfo),
]
