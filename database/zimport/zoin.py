from google.appengine.ext import db


class Zoin(db.Model):
    new_key   = db.StringProperty(db.Key())