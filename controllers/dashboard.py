from bo import *
from database import *

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

            tree.append({
                'link': '/tasks',
                'title': Translate('tasks')
            })

            tree.append({
                'link': '/questionary',
                'title':  Translate('questionaries'),
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