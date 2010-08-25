from google.appengine.ext import db
from google.appengine.ext import search

from database import *


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