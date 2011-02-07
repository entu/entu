from google.appengine.ext import db


class Zoin(db.Model):
    entity_kind = db.StringProperty()
    new_key     = db.StringProperty()

def AddZoin(entity_kind, old_key, new_key):
    z = Zoin(key_name = entity_kind + '__' + old_key)
    z.entity_kind = entity_kind
    z.new_key = str(new_key)
    z.put()

def GetZoin(entity_kind, old_key):
        z = Zoin().get_by_key_name(entity_kind + '__' + old_key)
        if z:
            key = z.new_key
            return db.get(key)