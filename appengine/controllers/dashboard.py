from bo import *
from database.bubble import *

class Show(boRequestHandler):
    def get(self):
        if self.authorize():

            tree = []

            tree.append({
                'link': 'http://www.artun.ee',
                'title': Translate('artun.ee'),
                'childs': [
                    {'link': 'http://gmail.artun.ee', 'title': Translate('inbox')},
                    {'link': 'http://calendar.artun.ee', 'title': Translate('calendar')},
                    {'link': 'http://docs.artun.ee', 'title': Translate('documents')},
                    {'link': '/oldauth?site=ois', 'title': '<b>' + Translate('old_ois') + '</b>'},
                ]
            })

            if self.authorize('bubbler'):
                bubbletypes = []
                for bt in db.Query(BubbleType).fetch(1000):
                    bubbletypes.append({
                        'link': '/bubbletype/%s' % bt.key().id(),
                        'title': bt.displayname,
                        'alt': db.Query(Bubble).filter('type', bt.type).filter('is_deleted', False).count(limit=1000000)
                    })
                bubbletypes = sorted(bubbletypes, key=lambda k: k['title'])

                tree.append({
                    'link': '/',
                    'title': Translate('bubbles'),
                    'childs': bubbletypes
                })

            if self.authorize('questionary') or self.authorize('reception'):
                tree.append({
                    'link': '',
                    'title': Translate('administration'),
                    'childs': [
                        {'link': '/reception', 'title': Translate('reception'), 'childs': [{
                            'link': '/application/stats', 'title': Translate('statistics')
                            }]},
                        {'link': '/questionary', 'title': Translate('questionaries')},
                    ]
                })

            self.view('dashboard', 'dashboard.html', {
                'tree': tree,
            })


def main():
    Route([
            ('/', Show)
        ])


if __name__ == '__main__':
    main()