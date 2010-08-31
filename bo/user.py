from google.appengine.ext import db
from google.appengine.ext import search
from google.appengine.api import users

from bo.user import *
from bo.settings import *


class User(db.Model):
    name            = db.StringProperty()
    email           = db.StringProperty()
    password        = db.StringProperty()
    identities      = db.StringListProperty()
    language        = db.StringProperty()
    avatar          = db.BlobProperty()
    activation_key  = db.StringProperty()

    def current(self):
        u = None
        user = users.get_current_user()

        if user and user.federated_identity():
            u = db.Query(User).filter('identities =', user.federated_identity()).get()
            if u and not u.language:
                u.language = SYSTEM_LANGUAGE
                u.save()

        if u:
            u.is_guest = False
        else:
            u = User()
            u.is_guest = True
            u.name = GUEST_NAME
            u.email = GUEST_EMAIL
            u.language = SYSTEM_LANGUAGE

        return u