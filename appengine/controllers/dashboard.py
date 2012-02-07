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

        bubbletypes = []
        for bt in db.Query(BubbleType).fetch(50):
            if db.Query(Bubble, keys_only=True).filter('type', bt.type).filter('viewers', Person().current).get():
                if bt.menugroup:
                    if bt.menugroup.value:
                        bubbletypes.append({
                            'group': bt.menugroup.value,
                            'link': '/bubble/%s' % bt.type,
                            'title': bt.name_plural.value,
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
