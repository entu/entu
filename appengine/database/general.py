from google.appengine.ext import db
#from google.appengine.ext import blobstore
#from google.appengine.api import images

from bo import *
from database.dictionary import *


class Location(ChangeLogModel):
    building            = db.ReferenceProperty(Dictionary, collection_name='location_buildings')
    room_number         = db.StringProperty()
    name                = db.ReferenceProperty(Dictionary, collection_name='location_names')
    model_version   = db.StringProperty(default='A')