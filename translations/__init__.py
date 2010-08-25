from translations.estonian import *

from database.person import *


def Translations(key = None):

    p = Person().current()
    if p:
        l = p.language

    if key:
        if key in TRANSLATION:
            return TRANSLATION[key].decode('utf8')
        else:
            return key
    else:
        return TRANSLATION