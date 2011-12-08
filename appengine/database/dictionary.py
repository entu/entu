from google.appengine.ext import db
from google.appengine.ext import search

from bo import *


class Dictionary(ChangeLogModel):
    name            = db.StringProperty()
    english         = db.TextProperty()
    estonian        = db.TextProperty()

    @property
    def value(self):
        language = UserPreferences().current.language
        return getattr(self, language) if getattr(self, language) else ''
