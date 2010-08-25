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
        curriculums = []

        if searchstr:
            curriculums = Curriculum.all().search(searchstr).fetch(100)

        bo.view(self, 'curriculums', 'curriculum_search.html', {'curriculums': curriculums, 'search': searchstr})


def main():
    bo.app([
            (r'/curriculum/search(.*)', Search),
            (r'/curriculum/(.*)', List)
        ])


if __name__ == '__main__':
    main()