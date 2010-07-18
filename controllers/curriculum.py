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

        if searchstr:
            curriculums = Curriculum.all().search(searchstr).fetch(100)

            boView(self, '', 'curriculum_search.html', {'curriculums': curriculums, 'search': searchstr})
        else:
            boView(self, '', 'curriculum_search.html')






def main():
    boWSGIApp([
            (r'/curriculum/search(.*)', Search),
            (r'/curriculum/(.*)', List)
        ])


if __name__ == '__main__':
    main()