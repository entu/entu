from google.appengine.ext import db

from bo import *


class Asset(ChangeLogModel):
    location        = db.StringProperty()
    room            = db.StringProperty()
    user            = db.StringProperty()
    asset_id        = db.StringProperty()
    datetime        = db.DateTimeProperty(auto_now_add=True)