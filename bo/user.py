from google.appengine.ext import db
from google.appengine.ext import search
from google.appengine.api import users


class User(db.Model):
    email           = db.StringProperty()
    identities      = db.StringListProperty()
    language        = db.StringProperty()
    avatar          = db.BlobProperty()
    activation_key  = db.StringProperty()

    def current(self):
        user = users.get_current_user()
        if user and user.federated_identity():
            return db.Query(User).filter('identities =', user.federated_identity()).get()

    def language(self):
        return 'english'