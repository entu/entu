from google.appengine.ext import db
from google.appengine.ext import search
from google.appengine.api import users

from database import *
from bo.user import *


class Person(search.SearchableModel):
    identities  = db.StringListProperty()
    forename    = db.StringProperty()
    surname     = db.StringProperty()
    idcode      = db.StringProperty()
    gender      = db.ReferenceProperty(Dictionary, collection_name='genders')
    birth_date  = db.DateProperty()
    user        = db.ReferenceProperty(User, collection_name='person')
#------
    access_log  = db.StringListProperty()


class Contact(db.Model):
    person          = db.ReferenceProperty(Person, collection_name='contacts')
    contact_type    = db.ReferenceProperty(Dictionary, collection_name='contact_types')
    value           = db.StringProperty()
#------
    access_log      = db.StringListProperty()


class Role(db.Model):
    name                    = db.StringProperty()
    controllers_to_read     = db.StringListProperty()
    controllers_to_write    = db.StringListProperty()
#------
    access_log              = db.StringListProperty()


class PersonRole(db.Model):
    start_date  = db.DateTimeProperty(auto_now_add=True)
    end_date    = db.DateTimeProperty(auto_now_add=True)
    person      = db.ReferenceProperty(Person, collection_name='roles')
    role        = db.ReferenceProperty(Role, collection_name='persons')
#------
    access_log  = db.StringListProperty()