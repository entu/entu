from boFunctions import *
from models import *
from forms import *

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

        boView(self, 'persons', 'person_search.html', {'persons': persons, 'search': searchstr})


def main():
    boWSGIApp([
            (r'/person/search(.*)', Search),
            (r'/person/(.*)', List)
        ])


if __name__ == '__main__':
    main()