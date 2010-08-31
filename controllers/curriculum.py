from bo import *
from database import *

from urllib import unquote


class List(webapp.RequestHandler):
    def get(self, a = None):
        b = a.split('/')
        print b[-2:]


class Search(webapp.RequestHandler):

    def get(self, searchstr = None):

        searchstr = unquote(searchstr).decode('utf8')[1:]
        curriculums = []

        if searchstr:
            curriculums = Curriculum.all().search(searchstr).fetch(100)

        View(self, 'curriculums', 'curriculum_search.html', {'curriculums': curriculums, 'search': searchstr})


def main():
    Route([
            (r'/curriculum/search(.*)', Search),
            (r'/curriculum/(.*)', List)
        ])


if __name__ == '__main__':
    main()