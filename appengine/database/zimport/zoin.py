from google.appengine.ext import db

from bo import *


class Zoin(db.Expando):
    entity_kind = db.StringProperty()
    new_entity  = db.ReferenceProperty()


def AddZoin(entity_kind, old_key, new_key):
    z = Zoin(key_name = entity_kind + '__' + old_key)
    z.entity_kind = entity_kind
    z.new_entity = new_key
    z.put()


def GetZoin(entity_kind, old_key):
    if entity_kind and old_key:
        z = Zoin().get_by_key_name(entity_kind + '__' + old_key)
        if z:
            try:
                return z.new_entity
            except:
                pass


def GetZoinKey(entity_kind, old_key):
    if entity_kind and old_key:
        z = Zoin().get_by_key_name(entity_kind + '__' + old_key)
        if z:
            return z.new_entity.key()


def GetZoinKeyList(entity_kind, old_keys):
    result = []
    if entity_kind and old_keys:
        for k in StrToList(old_keys):
            z = GetZoin(entity_kind, k)
            if z:
                result = ListMerge(z.key(), result)
    return result
