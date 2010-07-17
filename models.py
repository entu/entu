from google.appengine.ext import db
from google.appengine.ext import search
from google.appengine.api import users


# Common

class AccessLog(db.Model):
    date            = db.DateTimeProperty(auto_now_add=True)
    person          = db.StringProperty()
    property_name   = db.StringProperty()
    old_value       = db.StringProperty()
    new_value       = db.StringProperty()

class Dictionary(db.Model):
    name        = db.StringProperty()
#------
    access_log  = db.StringListProperty()

class Translation(search.SearchableModel):
    language    = db.StringProperty()
    value       = db.StringProperty()
    dictionary  = db.ReferenceProperty(Dictionary, collection_name='translations')
#------
    access_log  = db.StringListProperty()

class Classifier(db.Model):
    name        = db.StringProperty()
    value       = db.ReferenceProperty(Dictionary, collection_name='classifiers')
#------
    access_log  = db.StringListProperty()


# Person

class Person(search.SearchableModel):
    forename    = db.StringProperty()
    surname     = db.StringProperty()
    idcode      = db.StringProperty()
    gender      = db.StringProperty()
    birth_date  = db.DateProperty()
    identities  = db.StringListProperty()
#------
    access_log  = db.StringListProperty()

class PersonPreferences(db.Model):
    person      = db.ReferenceProperty(Person, collection_name='preferences')
    language    = db.ReferenceProperty(Classifier, collection_name='person_languages')
    avatar      = db.BlobProperty()
#------
    access_log  = db.StringListProperty()

class Contact(db.Model):
    person          = db.ReferenceProperty(Person, collection_name='contacts')
    type            = db.StringProperty()
    value           = db.StringProperty()
    activation_key  = db.StringProperty()
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


# Curriculum

class Curriculum(search.SearchableModel):
    name                    = db.ReferenceProperty(Dictionary, collection_name='curriculum_names')
    code                    = db.StringProperty()
    tags                    = db.StringListProperty()
    level_of_education      = db.ReferenceProperty(Classifier, collection_name='curriculum_level_of_educations')
    form_of_training        = db.ReferenceProperty(Classifier, collection_name='curriculum_form_of_trainings')
    nominal_years           = db.IntegerProperty()
    nominal_credit_points   = db.IntegerProperty()
    degree                  = db.ReferenceProperty(Classifier, collection_name='curriculum_degree')
    manager                 = db.ReferenceProperty(Person, collection_name='managed_curriculums')
#------
    access_log  = db.StringListProperty()


class RatingScale(db.Model):
    name        = db.ReferenceProperty(Dictionary, collection_name='curriculum_names')
#------
    access_log  = db.StringListProperty()


class Subject(search.SearchableModel):
    create_date     = db.DateTimeProperty(auto_now_add=True)
    code            = db.StringProperty()
    name            = db.StringProperty()
    tags            = db.StringListProperty()
    credit_points   = db.FloatProperty()
    rating_scale    = db.ReferenceProperty(RatingScale, collection_name='subjects')
#------
    access_log  = db.StringListProperty()