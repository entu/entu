from google.appengine.ext import db
from google.appengine.ext import search


class Dictionary(db.Model):
    name            = db.StringProperty()
    value           = db.StringProperty()
    languages       = db.StringListProperty(default=[]) """ list-property with language names of existing translations
                                                            to enable the functionality to find missing translations.
                                                            To find all curriculums, that have no french translation,
                                                            one could search for:
                                                                dictionary_name = 'curriculum_name'
                                                                languages != 'french' """
    model_version   = db.StringProperty(default='A')

    def translate(self):
        from bo import *

        t = db.Query(Translation).filter('dictionary', self).filter('language', UserPreferences().current.language).get()
        if t and t.value:
            return t.value
        else:
            return self.value


class Translation(search.SearchableModel):
    dictionary      = db.ReferenceProperty(Dictionary, collection_name='translations')
    dictionary_name = db.StringProperty()
    language        = db.StringProperty()
    value           = db.StringProperty(multiline=True)
    is_verified     = db.BooleanProperty()          """ When new dictionary object is created, the source translation
                                                        is marked as verified.
                                                        If multiple translations are merged, then all verified
                                                        translations remain the same and also remain marked as verified """
    model_version   = db.StringProperty(default='A')


def DictionaryAdd(name, value):
    if len(value) < 1:
        return None

    from bo import *
    language = UserPreferences().current.language

    t = db.Query(Translation).filter('dictionary_name', name).filter('value', value).filter('language', language).get()
    if t:
        return t.dictionary.key()

    d = db.Query(Dictionary).filter('name', name).filter('value', value.replace('\n',' ')).get()
    if not d:
        d = Dictionary()
        d.name = name
        d.value = value.replace('\n',' ')
        d.languages = []
    d.languages.append(language)
    d.put()

    t = Translation()
    t.dictionary = d
    t.dictionary_name = name
    t.language = language
    t.value = value
    t.save()

    return d.key()