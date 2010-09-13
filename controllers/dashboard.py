from bo import *
from database import *

class Show(webapp.RequestHandler):
    def get(self):

        c = []
        for l in db.Query(Translation).filter('dictionary_name', 'level_of_education').filter('language', User().current().language).order('value').fetch(100):
            c.append({
                'link': '/curriculum/level/' + str(l.dictionary.key()),
                'title': l.dictionary.translate(),
            })

        childs = []
        childs.append({
            'link': '/person',
            'title': Translate('persons'),
        })

        childs.append({
            'link': '/curriculum',
            'title': Translate('curriculums'),
            'childs': c
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
            ('/dashboard', Show)
        ])


if __name__ == '__main__':
    main()