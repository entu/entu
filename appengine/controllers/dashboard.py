from string import ascii_lowercase

from bo import *
from database.bubble import *


class Show(boRequestHandler):
    def get(self):
        self.authorize()

        person = Person().current
        person.grades_count = db.Query(Grade).filter('person', person).filter('is_deleted', False).count()

        self.view(
            main_template='main/index.html',
            template_file = 'dashboard.html',
            page_title = 'page_dashboard',
            values = {
                'person': person,
            }
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
                'title': Translate('menu_bubbles'),
                'childs': bubbletypes
            })

        if self.authorize('questionary') or self.authorize('reception'):
            menu.append({
                'title': Translate('menu_admin'),
                'childs': [
                    {'link': '/person', 'title': Translate('menu_persons')},
                    {'link': '/questionary', 'title': Translate('menu_feedback')},
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
