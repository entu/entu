import string
import csv
import cStringIO
from datetime import *

from bo import *
from database.bubble import *
from database.person import *
from database.dictionary import *

from django.template import TemplateDoesNotExist


class ShowBubbleTypeList(boRequestHandler):
    def get(self, url):
        if not self.authorize('bubbler'):
            return

        bubbletypes = db.Query(BubbleType).fetch(1000)

        try:
            self.view('application', 'bubbletype/bubbletype_list_' + Person().current.current_role.template_name + '.html', {
            'bubbletypes': bubbletypes,
        })
        except TemplateDoesNotExist:
            self.view('application', 'bubbletype/bubbletype_list.html', {
            'bubbletypes': bubbletypes,
        })


class ShowBubbleType(boRequestHandler):
    def get(self, id):
        if not self.authorize('bubbler'):
            return

        bubbletype = BubbleType().get_by_id(int(id))
        if not bubbletype:
            self.view('N/A', 'bubbletype/notfound.html', {
                'bubbletype_id': id,
            })
            return

        try:
            self.view('application', 'bubbletype/bubbletype_' + Person().current.current_role.template_name + '.html', {
            'bubbletype': bubbletype,
        })
        except TemplateDoesNotExist:
            self.view('application', 'bubbletype/bubbletype.html', {
            'bubbletype': bubbletype,
        })

    def post(self, key):
        if not self.authorize('bubbler'):
            return

        bubbletype = BubbleType().get(key)
        if not bubbletype:
            return

        field = self.request.get('field').strip()
        value = self.request.get('value').strip()
        if not value:
            setattr(bubbletype, field, None)
        else:
            if field in ['name', 'description']:
                setattr(bubbletype, field, DictionaryAdd(('bubbletype_' + field), value))
                if field == 'name':
                    bubbletype.sort_estonian = StringToSortable(value)
            if field in ['maximum_leecher_count', 'grade_display_method', 'is_exclusive']:
                setattr(bubbletype, field, value)
            if field == 'allowed_subtypes':
                bubbletype.allowed_subtypes = AddToList(db.Key(value), bubbletype.allowed_subtypes)

        bubbletype.put()
        bubbletype.displayname_cache_reset()



def main():
    Route([
            ('/btype/', ShowBubbleTypeList),
            (r'/btype/(.*)', ShowBubbleType),
        ])


if __name__ == '__main__':
    main()