from google.appengine.ext import db
from google.appengine.ext import search
from google.appengine.api import users
from datetime import datetime

from database.dictionary import *
from database.general import *


class Person(search.SearchableModel):
    apps_username       = db.StringProperty() # forename.surname@domain
    forename            = db.StringProperty()
    surname             = db.StringProperty()
    idcode              = db.StringProperty()
    gender              = db.ReferenceProperty(Dictionary, collection_name='genders')
    birth_date          = db.DateProperty()
    created             = db.DateTimeProperty(auto_now_add=True)
    last_seen           = db.DateTimeProperty()
    model_version       = db.StringProperty(default='A')

    @property
    def displayname(self):
        return ' '.join([self.forename, self.surname])

    @property
    def current(self):
        user = users.get_current_user()
        if user:
            person = db.Query(Person).filter('apps_username', user.email()).get()
            if not person:
                person = Person()
                person.apps_username = user.email()
                person.idcode = 'guest'
            person.last_seen = datetime.today()
            person.save()
            return person


class Department(db.Model):
    name                = db.ReferenceProperty(Dictionary, collection_name='department_names')
    is_academic         = db.BooleanProperty()
    parent_department   = db.SelfReferenceProperty(collection_name='child_departments')
    manager             = db.ReferenceProperty(Person, collection_name='managed_departments')
    model_version       = db.StringProperty(default='A')


class Contact(db.Model):
    person              = db.ReferenceProperty(Person, collection_name='contacts')
    type                = db.ReferenceProperty(Dictionary, collection_name='contact_types')
    value               = db.StringProperty()
    model_version       = db.StringProperty(default='A')


class Role(db.Model):
    name        = db.ReferenceProperty(Dictionary, collection_name='role_names')
    rights      = db.StringListProperty()
    model_version       = db.StringProperty(default='A')


class PersonRole(db.Model):
    person              = db.ReferenceProperty(Person, collection_name='roles')
    role                = db.ReferenceProperty(Role, collection_name='persons')
    department          = db.ReferenceProperty(Department, collection_name='persons')
    model_version       = db.StringProperty(default='A')


class PersonDocument(db.Model):
    person              = db.ReferenceProperty(Person, collection_name='documents')
    document            = db.ReferenceProperty(Document, collection_name='persons')
    relation            = db.ReferenceProperty(Dictionary, collection_name='person_document_relations')
    date_time           = db.DateTimeProperty(auto_now_add=True)
    model_version       = db.StringProperty(default='A')