from google.appengine.ext import db
from google.appengine.ext import search

from bo import *


class Dictionary(ChangeLogModel):
    name            = db.StringProperty()
    english         = db.TextProperty()
    estonian        = db.TextProperty()
    model_version   = db.StringProperty(default='A')

    @property
    def value(self):
        language = UserPreferences().current.language
        cache_key = 'DictionaryTranslation_' + language + '_' + str(self.key())
        translation = Cache().get(cache_key, False)
        if not translation:
            translation = getattr(self, language)
            Cache().set(cache_key, translation, False, 3600)
        return translation