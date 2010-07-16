from google.appengine.ext import db
from google.appengine.ext import search
from google.appengine.api import users


# Common

class Dictionary(search.SearchableModel):
    kind_name   = db.StringProperty()
    entity_key  = db.StringProperty()
    name        = db.StringProperty()
    language    = db.StringProperty()
    value       = db.StringProperty()

class Classifier(db.Model):
    create_date = db.DateTimeProperty(auto_now_add=True)
    name        = db.StringProperty()
    value       = db.ReferenceProperty(Dictionary, collection_name='classifiers')


# Person

class Person(search.SearchableModel):
    create_date = db.DateTimeProperty(auto_now_add=True)
    forename    = db.StringProperty()
    surname     = db.StringProperty()
    idcode      = db.StringProperty()
    gender      = db.ReferenceProperty(Classifier, collection_name='person_genders')
    birth_date  = db.DateProperty()
    identities  = db.StringListProperty()

class PersonPreferences(db.Model):
    person      = db.ReferenceProperty(Person, collection_name='preferences')
    language    = db.StringProperty()
    avatar      = db.BlobProperty()

class Contact(db.Model):
    create_date     = db.DateTimeProperty(auto_now_add=True)
    person          = db.ReferenceProperty(Person, collection_name='contacts')
    type            = db.ReferenceProperty(Classifier, collection_name='contact_types')
    value           = db.StringProperty()
    activation_key  = db.StringProperty()

class Role(db.Model):
    name                    = db.StringProperty()
    controllers_to_read     = db.StringListProperty()
    controllers_to_write    = db.StringListProperty()

class PersonRole(db.Model):
    start_date  = db.DateTimeProperty(auto_now_add=True)
    end_date    = db.DateTimeProperty(auto_now_add=True)
    person      = db.ReferenceProperty(Person, collection_name='roles')
    role        = db.ReferenceProperty(Role, collection_name='persons')


# Curriculum

class Curriculum(search.SearchableModel):
    name                    = db.StringProperty()
    code                    = db.StringProperty()
    tags                    = db.StringListProperty()
    level_of_education      = db.ReferenceProperty(Classifier, collection_name='curriculum_level_of_educations')
    form_of_training        = db.ReferenceProperty(Classifier, collection_name='curriculum_form_of_trainings')
    nominal_years           = db.IntegerProperty()
    nominal_credit_points   = db.IntegerProperty()
    degree                  = db.ReferenceProperty(Classifier, collection_name='curriculum_degree')
    manager                 = db.ReferenceProperty(Person, collection_name='managed_curriculums')


class RatingScale(db.Model):
    name            = db.StringProperty()


class Subject(search.SearchableModel):
    create_date     = db.DateTimeProperty(auto_now_add=True)
    code            = db.StringProperty()
    name            = db.StringProperty()
    tags            = db.StringListProperty()
    credit_points   = db.FloatProperty()
    rating_scale    = db.ReferenceProperty(RatingScale, collection_name='subjects')