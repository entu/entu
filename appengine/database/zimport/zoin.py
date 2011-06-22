from google.appengine.ext import db

from bo import *


class Zoin(db.Model):
    entity_kind = db.StringProperty()
    new_key     = db.StringProperty()


def AddZoin(entity_kind, old_key, new_key):
    z = Zoin(key_name = entity_kind + '__' + old_key)
    z.entity_kind = entity_kind
    z.new_key = str(new_key)
    z.put()


def GetZoin(entity_kind, old_key):
    if entity_kind and old_key:
        z = Zoin().get_by_key_name(entity_kind + '__' + old_key)
        if z:
            return db.get(z.new_key)


def GetZoinKey(entity_kind, old_key):
    if entity_kind and old_key:
        z = Zoin().get_by_key_name(entity_kind + '__' + old_key)
        if z:
            return db.Key(z.new_key)


def GetZoinKeyList(entity_kind, old_keys):
    result = []
    if entity_kind and old_keys:
        for k in StrToList(old_keys):
            z = GetZoin(entity_kind, k)
            if z:
                result = AddToList(z.key(), result)
    return result