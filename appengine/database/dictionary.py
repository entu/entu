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


def GetDictionaryValue(key=None, language=None):
    if not key:
        return ''
    d = Dictionary().get(key)
    if not d:
        return ''
    returnvalue = getattr(d, language, '') if language else getattr(d, UserPreferences().current.language, '')
    if not returnvalue:
        return ''

    return returnvalue


def GetDictionaryName(key=None):
    if not key:
        return ''
    d = Dictionary().get(key)
    if not d:
        return ''
    returnvalue = getattr(d, 'name', '')
    if not returnvalue:
        return ''

    return returnvalue