from bo import *
from database import *

class Show(boRequestHandler):
    def get(self):
        if self.authorize():

            childs = []
            childs.append({
                'link': '/person',
                'title': Translate('persons'),
            })

            childs.append({
                'link': '/curriculum',
                'title': Translate('curriculums'),
            })

            childs.append({
                'link': '/questionary',
                'title': Translate('questionaries'),
            })

            tree = {
                'link': SYSTEM_URL,
                'title': SYSTEM_TITLE,
                'columns': 3,
                'childs': childs,
            }

            self.view('dashboard', 'dashboard.html', {
                'tree': tree,
            })


def main():
    Route([
            ('/', Show)
        ])


if __name__ == '__main__':
    main()