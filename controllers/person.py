import bo
from database import *

import urllib


class List(bo.webapp.RequestHandler):
    def get(self, a = None):
        b = a.split('/')
        print b[-2:]


class Search(bo.webapp.RequestHandler):

    def get(self, searchstr = None):

        searchstr = urllib.unquote(searchstr).decode('utf8')[1:]
        persons = []

        if searchstr:
            persons = Person.all().search(searchstr).fetch(100)

        count = db.Query(Contact).count()

        bo.view(self, 'persons', 'person_search.html', {'persons': persons, 'search': searchstr, 'count': count})


def main():
    bo.app([
            (r'/person/search(.*)', Search),
            (r'/person/(.*)', List)
        ])


if __name__ == '__main__':
    main()