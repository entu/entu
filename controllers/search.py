from google.appengine.api import memcache

from urllib import unquote

from helpers import *
from database import *


class Search(webapp.RequestHandler):

    def get(self, searchstr = None):

        searchstr = unquote(searchstr).decode('utf8').strip('/')
        if searchstr == '':
            self.redirect ('/')

        tree = memcache.get('search_' + searchstr)
        if not tree:

            persons = []
            for p in Person.all().search(searchstr).order('forename').order('surname').fetch(100):             persons.append({
                    'link': '/person/' + str(p.key()),
                    'title': p.forename + ' ' + p.surname,
                })

            curriculums = []
            for l in Translation.all().search(searchstr).order('value').filter('dictionary_name', 'curriculum_name').fetch(100):
                curriculums.append({
                    'link': '/curriculum/' + str(l.key()),
                    'title': l.dictionary.translate(),
                    'alt': l.dictionary.curriculum_names[0].level_of_education.translate()
                })

            childs = []
            childs.append({
                'link': '/person',
                'title': Translate('persons'),
                'childs': persons,
            })

            childs.append({
                'link': '/curriculum',
                'title': Translate('curriculums'),
                'childs': curriculums
            })

            tree = {
                'link': SYSTEM_URL,
                'title': SYSTEM_TITLE,
                'columns': 3,
                'childs': childs,
            }

            memcache.add('search_' + searchstr, tree, 300)

        View(self, 'search', 'search.html', {
            'tree': tree,
        })




    def post(self, searchstr = None):
        self.redirect('/search/' + self.request.POST['search'])


def main():
    Route([
            (r'/search(.*)', Search),
        ])


if __name__ == '__main__':
    main()