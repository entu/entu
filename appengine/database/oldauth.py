from google.appengine.ext import db

from bo import *


class OldAuth(ChangeLogModel):
    site        = db.StringProperty()
    salt        = db.StringProperty(default='')
    loginurl    = db.StringProperty()
    logouturl   = db.StringProperty()
    version     = db.StringProperty(default='A')
