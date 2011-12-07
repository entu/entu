from google.appengine.ext import db

from bo import *


class OldAuth(ChangeLogModel):
    site            = db.StringProperty()
    url_login       = db.StringProperty()
    url_logout      = db.StringProperty()
    url_error       = db.StringProperty()
    salt            = db.StringProperty(default='')
    valid_domains   = db.StringListProperty()
