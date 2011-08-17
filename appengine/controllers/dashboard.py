from bo import *
from database.bubble import *


class Show(boRequestHandler):
    def get(self):
        self.view(
            page_title = 'dashboard',
            templatefile = 'dashboard.html',
        )


class ShowMenu(boRequestHandler):
    def get(self):
        menu = []

        menu.append({
            'title': Translate('artun.ee'),
            'childs': [
                {'link': 'http://gmail.artun.ee', 'title': Translate('inbox')},
                {'link': 'http://calendar.artun.ee', 'title': Translate('calendar')},
                {'link': 'http://docs.artun.ee', 'title': Translate('documents')},
                {'link': '/oldauth?site=ois', 'title': Translate('old_ois')},
            ]
        })

        if self.authorize('bubbler'):
            bubbletypes = []
            #for bt in sorted(db.Query(BubbleType).fetch(1000), key=attrgetter('displayname')):
            for bt in db.Query(BubbleType).fetch(50):
                bubbletypes.append({
                    'link': '/bubble/type/%s' % bt.type,
                    'title': bt.displayname,
                })

            menu.append({
                'title': Translate('bubbles'),
                'childs': bubbletypes
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
            templatefile = 'main_menu.html',
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