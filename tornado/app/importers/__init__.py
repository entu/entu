from google.appengine.api import memcache

from importers.ester import *
from importers.rahvaraamat import *
from importers.raamatukoi import *
from importers.googlebooks import *


def ImageByISBN(isbn):
    url = memcache.get('item_image_' + isbn)
    if not url:
        url = RahvaraamatImageByISBN(isbn)
        if not url:
            url = RaamatukoiImageByISBN(isbn)
            if not url:
                url = GoogleImageByISBN(isbn)

        if url:
            memcache.add(
                key = 'item_image_' + isbn,
                value = url,
                time = 3600
            )

    return url