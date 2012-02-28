from string import ascii_lowercase

from bo import *
from database.bubble import *
from database.dictionary import *


class Show(boRequestHandler):
    def get(self):
        self.view(
            main_template='main/index.html',
            template_file = 'dashboard.html',
            page_title = 'page_dashboard',
        )


class ShowMenu(boRequestHandler):
    def get(self):
        menu = []

        bubbletypes = []
        for bt in db.Query(Bubble).filter('type', 'bubble_type').fetch(100):
            if getattr(bt, 'menugroup', None) and getattr(bt, 'path', None):
                display = False
                if display == False:
                    if db.Query(Bubble, keys_only=True).filter('x_type', bt.key()).filter('x_br_viewer', CurrentUser().key()).get():
                        display = True
                if display == False:
                    if db.Query(Bubble, keys_only=True).filter('x_type', bt.key()).filter('x_br_subbubbler', CurrentUser().key()).get():
                        display = True
                if display == False:
                    if db.Query(Bubble, keys_only=True).filter('x_type', bt.key()).filter('x_br_editor', CurrentUser().key()).get():
                        display = True
                if display == False:
                    if db.Query(Bubble, keys_only=True).filter('x_type', bt.key()).filter('x_br_owner', CurrentUser().key()).get():
                        display = True
                if display == True:
                    bubbletypes.append({
                        'group': GetDictionaryValue(bt.menugroup) if getattr(bt, 'menugroup', None) else 'XYZ',
                        'link': '/bubble/%s' % bt.path,
                        'title': GetDictionaryValue(bt.name_plural),
                    })

        self.view(
            template_file = 'main/menu.html',
            main_template = None,
            values = {
                'bubbletypes': bubbletypes,
            }
        )


def main():
    Route([
            ('/', Show),
            ('/dashboard/menu', ShowMenu),
        ])


if __name__ == '__main__':
    main()
