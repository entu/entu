from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.api import images

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
    file            = blobstore.BlobReferenceProperty()
    external_link   = db.StringProperty()
    types           = db.StringListProperty()
    entities        = db.StringListProperty()
    title           = db.ReferenceProperty(Dictionary, collection_name='document_titles')
    uploader        = db.StringProperty()
    owners          = db.StringListProperty()
    editors         = db.StringListProperty()
    viewers         = db.StringListProperty()
    created         = db.DateTimeProperty(auto_now_add=True)

    @property
    def url(self):
        try:
            image_types = ('image/bmp', 'image/jpeg', 'image/pjpeg', 'image/png', 'image/gif', 'image/tiff', 'image/x-icon')
            if self.file.content_type in image_types:
                return images.get_serving_url(self.file.key())
            else:
                return '/document/' + str(self.key())
        except:
            pass