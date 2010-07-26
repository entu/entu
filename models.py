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
    value       = db.StringProperty()
#------
    access_log  = db.StringListProperty()

class Translation(search.SearchableModel):
    dictionary      = db.ReferenceProperty(Dictionary, collection_name='translations')
    language        = db.StringProperty()
    value           = db.StringProperty()
#------
    access_log  = db.StringListProperty()



# Person

class Person(search.SearchableModel):
    forename    = db.StringProperty()
    surname     = db.StringProperty()
    idcode      = db.StringProperty()
    gender      = db.ReferenceProperty(Dictionary, collection_name='genders')
    birth_date  = db.DateProperty()
    identities  = db.StringListProperty()
#------
    access_log  = db.StringListProperty()

class PersonPreferences(db.Model):
    person      = db.ReferenceProperty(Person, collection_name='preferences')
    language    = db.ReferenceProperty(Dictionary, collection_name='person_languages')
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
    name                    = db.ReferenceProperty(Dictionary, collection_name='curriculums')
    code                    = db.StringProperty()
    tags                    = db.StringListProperty()
    level_of_education      = db.ReferenceProperty(Dictionary, collection_name='curriculum_level_of_educations')
    form_of_training        = db.ReferenceProperty(Dictionary, collection_name='curriculum_form_of_trainings')
    nominal_years           = db.IntegerProperty()
    nominal_credit_points   = db.FloatProperty()
    degree                  = db.ReferenceProperty(Dictionary, collection_name='curriculum_degrees')
    manager                 = db.ReferenceProperty(Person, collection_name='managed_curriculums')
#------
    access_log  = db.StringListProperty()


class Orientation(search.SearchableModel):
    name            = db.ReferenceProperty(Dictionary, collection_name='orientations')
    code            = db.StringProperty()
    tags            = db.StringListProperty()
    curriculum      = db.ReferenceProperty(Curriculum, collection_name='orientations')
    manager         = db.ReferenceProperty(Person, collection_name='managed_orientations')
#------
    access_log      = db.StringListProperty()


class StudentOrientation(db.Model):
    student     = db.ReferenceProperty(Person, collection_name='orientations')
    orientation = db.ReferenceProperty(Orientation, collection_name='students')
    start_date  = db.DateTimeProperty(auto_now_add=True)
    end_date    = db.DateTimeProperty(auto_now_add=True)
#------
    access_log  = db.StringListProperty()


class RatingScale(db.Model):
    name        = db.ReferenceProperty(Dictionary, collection_name='rating_scales')
#------
    access_log  = db.StringListProperty()


class GradeDefinition(db.Model):
    name            = db.ReferenceProperty(Dictionary, collection_name='grade_definitions')
    positive        = db.BooleanProperty()
    equivivalent    = db.RatingProperty()
    scale           = db.ReferenceProperty(RatingScale, collection_name='grades')
#------
    access_log      = db.StringListProperty()


class Subject(search.SearchableModel):
    name            = db.ReferenceProperty(Dictionary, collection_name='subjects')
    code            = db.StringProperty()
    tags            = db.StringListProperty()
    credit_points   = db.FloatProperty()
    rating_scale    = db.ReferenceProperty(RatingScale, collection_name='subjects')
    manager         = db.ReferenceProperty(Person, collection_name='managed_subjects')
#------
    access_log      = db.StringListProperty()


class Module(search.SearchableModel):
    name                    = db.ReferenceProperty(Dictionary, collection_name='modules')
    code                    = db.StringProperty()
    tags                    = db.StringListProperty()
    manager                 = db.ReferenceProperty(Person, collection_name='managed_modules')
    minimum_credit_points   = db.FloatProperty()
    minimum_subject_count   = db.IntegerProperty()
#------
    access_log              = db.StringListProperty()


class ModuleOrientation(db.Model):
    mandatory   = db.BooleanProperty()
    module      = db.ReferenceProperty(Module, collection_name='orientations')
    orientation = db.ReferenceProperty(Orientation, collection_name='modules')
#------
    access_log  = db.StringListProperty()


class ModuleSubject(db.Model):
    mandatory   = db.BooleanProperty()
    module      = db.ReferenceProperty(Module, collection_name='subjects')
    subject     = db.ReferenceProperty(Subject, collection_name='modules')
#------
    access_log  = db.StringListProperty()


class SubjectSession(db.Model):
    subscription_start_date = db.DateTimeProperty(auto_now_add=True)
    subscription_end_date   = db.DateTimeProperty(auto_now_add=True)
    subject_start_date      = db.DateTimeProperty(auto_now_add=True)
    subject_end_date        = db.DateTimeProperty(auto_now_add=True)
    subject                 = db.ReferenceProperty(Subject, collection_name='sessions')
#------
    access_log              = db.StringListProperty()


class Subscription(db.Model):
    person      = db.ReferenceProperty(Person, collection_name='subscriptions')
    session     = db.ReferenceProperty(SubjectSession, collection_name='subscribed_subjects')
#------
    access_log  = db.StringListProperty()


