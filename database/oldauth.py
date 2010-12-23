from google.appengine.ext import db


class OldAuth(db.Model):
    site        = db.StringProperty()
    salt        = db.StringProperty(default='')
    loginurl    = db.StringProperty()
    logouturl   = db.StringProperty()
    version     = db.StringProperty(default='A')