from bo import *
from database import *

class Show(webapp.RequestHandler):
    def get(self):

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

        View(self, 'dashboard', 'dashboard.html', {
            'tree': tree,
        })


def main():
    Route([
            ('/', Show)
        ])


if __name__ == '__main__':
    main()