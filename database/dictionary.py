from google.appengine.ext import db
from google.appengine.ext import search

import bo


class Dictionary(db.Model):
    name        = db.StringProperty()
    value       = db.StringProperty()
#------
    access_log  = db.StringListProperty()


    def translate(self):
        t = db.Query(Translation).filter('dictionary = ', self).filter('language =', bo.User().language()).get()

        if t and t.value:
            return t.value
        else:
            return self.value


class Translation(search.SearchableModel):
    dictionary      = db.ReferenceProperty(Dictionary, collection_name='translations')
    language        = db.StringProperty()
    value           = db.StringProperty()
#------
    access_log  = db.StringListProperty()