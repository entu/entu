from google.appengine.api import urlfetch
from django.utils import simplejson


def GoogleImageByISBN(isbn):
    try:
        url = 'http://books.google.com/books?jscmd=viewapi&callback=a&bibkeys=ISBN:' + isbn
        content = urlfetch.fetch(url, deadline=10).content[2:][:-2]

        book = []
        for key, value in simplejson.loads(content).iteritems():
            book.append(value)

        if len(book) > 0:
            if 'thumbnail_url' in book[0]:
                return book[0]['thumbnail_url']

    except:
        pass
