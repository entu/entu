from google.appengine.ext import db
from google.appengine.ext import search
from google.appengine.api import users

from settings import *
from database.dictionary import *


class Person(search.SearchableModel):
    google_user_id  = db.StringProperty()
    forename        = db.StringProperty()
    surname         = db.StringProperty()
    idcode          = db.StringProperty()
    gender          = db.ReferenceProperty(Dictionary, collection_name='genders')
    birth_date      = db.DateProperty()
    language        = db.StringProperty(default=SYSTEM_LANGUAGE)
    last_seen       = db.DateTimeProperty()

    def current(self):
        user = users.get_current_user()
        if user:
            p = db.Query(Person).filter('google_user_id =', user.user_id()).get()
            if p:
                p.last_seen = datetime.today()
                p.save()
                return p


class Department(db.Model):
    name                = db.ReferenceProperty(Dictionary, collection_name='department_names')
    is_academic         = db.BooleanProperty()
    parent_department   = db.SelfReferenceProperty(collection_name='child_departments')
    manager             = db.ReferenceProperty(Person, collection_name='managed_departments')


class Contact(db.Model):
    person      = db.ReferenceProperty(Person, collection_name='contacts')
    type        = db.ReferenceProperty(Dictionary, collection_name='contact_types')
    value       = db.StringProperty()


class Role(db.Model):
    name        = db.ReferenceProperty(Dictionary, collection_name='role_names')


class PersonRole(db.Model):
    person      = db.ReferenceProperty(Person, collection_name='roles')
    role        = db.ReferenceProperty(Role, collection_name='persons')
    department  = db.ReferenceProperty(Department, collection_name='persons')


class Grade(db.Model):
    student         = db.ReferenceProperty(Person, collection_name='grades')
    date            = db.DateProperty()
    name            = db.ReferenceProperty(Dictionary, collection_name='grade_names')
    equivalent      = db.IntegerProperty()
    credit_points   = db.FloatProperty()
    school          = db.ReferenceProperty(Dictionary, collection_name='school_names')
    subject         = db.ReferenceProperty(Dictionary, collection_name='grade_subject_names')
    teacher_name    = db.StringProperty()