from string import ascii_lowercase

from bo import *
from database.bubble import *


class Show(boRequestHandler):
    def get(self):
        self.view(
            page_title = 'dashboard',
            template_file = 'dashboard.html',
        )


class ShowMenu(boRequestHandler):
    def get(self):
        menu = []

        if self.authorize('bubbler'):
            bubbletypes = []
            for bt in db.Query(BubbleType).fetch(50):
                bubbletypes.append({
                    'link': '/bubble/%s' % bt.type,
                    'title': bt.displayname,
                })
            menu.append({
                'title': Translate('bubbles'),
                'childs': bubbletypes
            })

        if self.authorize('bubbler'):
            persontypes = []
            for l in ['male', 'female']:
                persontypes.append({
                    'link': '/person/%s' % l,
                    'title': Translate('gender_' + l),
                })
            menu.append({
                'title': Translate('persons'),
                'childs': persontypes
            })

        if self.authorize('questionary') or self.authorize('reception'):
            menu.append({
                'title': Translate('administration'),
                'childs': [
                    {'link': '/reception', 'title': Translate('reception')},
                    {'link': '/reception/stats', 'title': Translate('statistics')},
                    {'link': '/questionary', 'title': Translate('questionaries')},
                ]
            })

        self.view(
            template_file = 'main/menu.html',
            main_template = None,
            values = {
                'menu': menu,
            }
        )


def main():
    Route([
            ('/', Show),
            ('/dashboard/menu', ShowMenu),
        ])


if __name__ == '__main__':
    main()
