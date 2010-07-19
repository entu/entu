from boFunctions import *
from models import *
from forms import *

import urllib


class Search(webapp.RequestHandler):

    def get(self, searchstr = None):

        searchstr = urllib.unquote(searchstr).decode('utf8')[1:]
        d = []
        form = DictionariesForm()

        if searchstr:
            d = Dictionary.all().search(searchstr).fetch(100)

        boView(self, 'dictionary', 'dictionary_search.html', {'dictionaries': d, 'search': searchstr, 'form': form})


def main():
    boWSGIApp([
            (r'/dictionary/search(.*)', Search),
        ])


if __name__ == '__main__':
    main()