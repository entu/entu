from google.appengine.ext import db
from google.appengine.ext import search

from bo.user import *


class Dictionary(db.Model):
    name        = db.StringProperty()
    value       = db.StringProperty()
    languages   = db.StringListProperty()

    def translate(self):
        t = db.Query(Translation).filter('dictionary = ', self).filter('language =', User().current().language).get()

        if t and t.value:
            return t.value
        else:
            return self.value


class Translation(search.SearchableModel):
    dictionary      = db.ReferenceProperty(Dictionary, collection_name='translations')
    dictionary_name = db.StringProperty()
    language        = db.StringProperty()
    value           = db.StringProperty()