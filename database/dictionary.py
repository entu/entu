from google.appengine.ext import db
from google.appengine.ext import search

from database import *


class Dictionary(db.Model):
    name        = db.StringProperty()
    value       = db.StringProperty()
#------
    access_log  = db.StringListProperty()

    def __get__(self):
        if self.value:
            t = db.Query(Translation).filter('dictionary = ', self).filter('language =', Person().language()).get()

            if t and t.value:
                self.value2 = t.value
            else:
                self.value2 = self.value


class Translation(search.SearchableModel):
    dictionary      = db.ReferenceProperty(Dictionary, collection_name='translations')
    language        = db.StringProperty()
    value           = db.StringProperty()
#------
    access_log  = db.StringListProperty()