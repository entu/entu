from google.appengine.ext import db
from google.appengine.ext import search

from bo import *


class Dictionary(ChangeLogModel):
    name            = db.StringProperty()
    english         = db.StringProperty(multiline=True)
    estonian        = db.StringProperty(multiline=True)
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

    def translate(self):
        return self.estonian
        """language = UserPreferences().current.language
        cache_key = 'dTranslation_' + language + '_' + str(self.key())
        translation = Cache().get(cache_key, False)
        if not translation:
            translation = getattr(self, language)
            Cache().set(cache_key, translation, False, 3600)
        return translation"""

    def add(self):
        d = db.Query(Dictionary).filter('name', self.name).filter('estonian', self.estonian).filter('english', self.english).get()
        if not d:
            self.put()
            d = self
        return d



def DictionaryAdd(name, value):
    if len(value) < 1:
        return None

    from bo import *
    language = UserPreferences().current.language

    d = db.Query(Dictionary).filter('name', name).filter(language, value).get()
    if not d:
        d = Dictionary()
        d.name = name
        setattr(d, language, value)
        d.put()

    return d.key()