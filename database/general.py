from google.appengine.ext import db
from google.appengine.ext import search


class AccessLog(db.Model):
    date            = db.DateTimeProperty(auto_now_add=True)
    person          = db.StringProperty()
    property_name   = db.StringProperty()
    old_value       = db.StringProperty()
    new_value       = db.StringProperty()