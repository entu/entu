from google.appengine.ext import db
from google.appengine.ext import blobstore

from database.dictionary import *


class AccessLog(db.Model):
    kind_name       = db.StringProperty()
    entity_key      = db.StringProperty()
    property_name   = db.StringProperty()
    system_user_key = db.StringProperty()
    datetime        = db.DateTimeProperty(auto_now_add=True)
    old_value       = db.StringProperty()
    new_value       = db.StringProperty()
    model_version   = db.StringProperty(default='A')

    def add(kind_name, entity_key, property_name, old_value, new_value):
        al = AccessLog()
        al.kind_name = kind_name
        al.entity_key = entity_key
        al.property_name = property_name
        al.old_value = old_value
        al.new_value = new_value

        user = users.get_current_user()
        if user:
            system_user_key = user.email()

        al.save()
        return al.key()


class Location(db.Model):
    building            = db.ReferenceProperty(Dictionary, collection_name='location_buildings')
    room_number         = db.StringProperty()
    name                = db.ReferenceProperty(Dictionary, collection_name='location_names')


class Document(db.Model):
    title       = db.ReferenceProperty(Dictionary, collection_name='document_titles')
    type        = db.ReferenceProperty(Dictionary, collection_name='document_types')
    document    = blobstore.BlobReferenceProperty()
    entities    = db.StringListProperty()