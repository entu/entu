from helpers import *
from database import *

import urllib


class ShowPersonStart(webapp.RequestHandler):

    def get(self):

        levels = []
        for l in db.Query(Translation).filter('dictionary_name', 'level_of_education').filter('language', User().current().language).order('value').fetch(100):
            levels.append({
                'link': '/person/level/' + str(l.key()),
                'title': l.dictionary.translate(),
            })

        childs = []
        childs.append({
            'link': '/person',
            'title': Translate('level_of_education'),
            'childs': levels
        })
        childs.append({
            'link': '/person',
            'title': Translate('facuty'),
        })
        childs.append({
            'link': '/person',
            'title': Translate('role'),
        })



        tree = {
            'link': SYSTEM_URL,
            'title': SYSTEM_TITLE,
            'columns': 3,
            'childs': childs,
        }

        View(self, 'persons', 'person.html', {
            'tree': tree,
            'levels': levels
        })


class ShowPerson(webapp.RequestHandler):

    def get(self, key = None):

        p = db.Query(Person).filter('__key__', db.Key(key.strip('/'))).get()

        View(self, p.forename + ' ' + p.surname, 'person_tree.html', {
            'person': p,
        })


def main():
    Route([
            ('/person', ShowPersonStart),
            (r'/person(.*)', ShowPerson),
        ])


if __name__ == '__main__':
    main()