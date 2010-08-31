from bo import *
from database import *


class Search(webapp.RequestHandler):

    def get(self):

        p = Person.all().filter(searchstr).fetch(100)

        count = Person.all().count()

        View(self, 'persons', 'person_search.html', {'persons': persons, 'search': searchstr, 'count': count})


def main():
    Route([
            (r'/update', Update),
        ])


if __name__ == '__main__':
    main()