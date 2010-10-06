from google.appengine.ext import db
from google.appengine.ext import search
from google.appengine.api import users
from datetime import datetime

from bo.user import *
from bo.settings import *


class User(db.Model):
    google_user_id  = db.StringProperty()
    email           = db.StringProperty()
    nickname        = db.StringProperty()
    language        = db.StringProperty(default=SYSTEM_LANGUAGE)
    created         = db.DateTimeProperty(auto_now_add=True)
    last_seen       = db.DateTimeProperty()

    def current(self):
        user = users.get_current_user()
        if user:
            u = db.Query(User).filter('user_id =', user.user_id()).get()
            if not u:
                u = User()
                u.user_id = user.user_id()
                u.email = user.email()
                u.nickname = user.nickname()

            u.last_seen = datetime.today()
            u.put()

            return u