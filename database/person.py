from google.appengine.ext import db
from google.appengine.ext import search
from google.appengine.ext import blobstore
from google.appengine.api import users
from datetime import datetime

from database.dictionary import *
from database.general import *
from libraries.gmemsess import *


class Person(search.SearchableModel):
    apps_username           = db.StringProperty() # forename.surname@domain
    email                   = db.StringProperty()
    password                = db.StringProperty()
    forename                = db.StringProperty()
    surname                 = db.StringProperty()
    idcode                  = db.StringProperty()
    gender                  = db.StringProperty(choices=['', 'male', 'female'])
    birth_date              = db.DateProperty()
    created                 = db.DateTimeProperty(auto_now_add=True)
    have_been_subsidised    = db.BooleanProperty(default=False)
    last_seen               = db.DateTimeProperty()
    model_version           = db.StringProperty(default='A')

    @property
    def displayname(self):
        return ' '.join([self.forename, self.surname])

    @property
    def photo(self):
        return db.Query(Document).filter('types', 'person_photo').filter('entities', str(self.key())).get()

    @property
    def contacts(self):
        return db.Query(Contact).ancestor(self).fetch(1000)

    @property
    def current(self, web=None):
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


    def current_s(self, web):
        if self.current:
            return self.current
        else:
            sess = Session(web, timeout=86400)
            if 'application_person_key' in sess:
                return Person().get(sess['application_person_key'])


class Cv(db.Model):
    type                = db.StringProperty(choices=['secondary_education', 'higher_education', 'workplace'])
    organisation        = db.StringProperty()
    start               = db.StringProperty()
    end                 = db.StringProperty()
    description         = db.StringProperty()
    model_version       = db.StringProperty(default='A')


class Department(db.Model):
    name                = db.ReferenceProperty(Dictionary, collection_name='department_names')
    is_academic         = db.BooleanProperty()
    parent_department   = db.SelfReferenceProperty(collection_name='child_departments')
    manager             = db.ReferenceProperty(Person, collection_name='managed_departments')
    model_version       = db.StringProperty(default='A')


class Contact(db.Model):
    #person              = db.ReferenceProperty(Person, collection_name='contacts')
    type                = db.StringProperty(choices=['email', 'phone', 'address', 'skype'])
    value               = db.StringProperty()
    model_version       = db.StringProperty(default='A')


class Role(db.Model):
    name            = db.ReferenceProperty(Dictionary, collection_name='role_names')
    rights          = db.StringListProperty()
    model_version   = db.StringProperty(default='A')


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