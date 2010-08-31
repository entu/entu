from bo import *
from database import *

import urllib


class List(webapp.RequestHandler):
    def get(self, a = None):
        b = a.split('/')
        print b[-2:]


class Search(webapp.RequestHandler):

    def get(self, searchstr = None):

        searchstr = urllib.unquote(searchstr).decode('utf8')[1:]
        persons = []

        if searchstr:
            persons = Person.all().search(searchstr).fetch(100)

        count = Person.all().count()

        View(self, 'persons', 'person_search.html', {'persons': persons, 'search': searchstr, 'count': count})


def main():
    Route([
            (r'/person/search(.*)', Search),
            (r'/person/(.*)', List)
        ])


if __name__ == '__main__':
    main()