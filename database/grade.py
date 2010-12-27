from google.appengine.ext import db
from google.appengine.ext import search
from google.appengine.api import users
from datetime import datetime

from database.dictionary import *
from database.general import *
from database.person import *


class Grade(db.Model):
    student         = db.ReferenceProperty(Person, collection_name='received_grades')
    teacher         = db.ReferenceProperty(Person, collection_name='given_grades')
    date            = db.DateProperty()
    name            = db.ReferenceProperty(Dictionary, collection_name='grade_names')
    equivalent      = db.IntegerProperty()
    credit_points   = db.FloatProperty()
    school          = db.ReferenceProperty(Dictionary, collection_name='school_names')
    subject         = db.ReferenceProperty(Dictionary, collection_name='grade_subject_names')
    teacher_name    = db.StringProperty()
    model_version   = db.StringProperty(default='A')


class RatingScale(db.Model):
    name            = db.ReferenceProperty(Dictionary, collection_name='rating_scale_names')
    model_version   = db.StringProperty(default='A')


class GradeDefinition(db.Model):
    rating_scale    = db.ReferenceProperty(RatingScale, collection_name='grade_definitions')
    name            = db.ReferenceProperty(Dictionary, collection_name='grade_definition_names')
    is_positive     = db.BooleanProperty()
    equivalent      = db.IntegerProperty()
    model_version   = db.StringProperty(default='A')


class Exam(db.Model):
    name                    = db.ReferenceProperty(Dictionary, collection_name='exam_names')
    description             = db.ReferenceProperty(Dictionary, collection_name='exam_descriptions')
    examiner                = db.ReferenceProperty(Person, collection_name='examiner_of_exams')
    registration_start_date = db.DateProperty()
    rankings_date           = db.DateProperty()
    type                    = db.ReferenceProperty(Dictionary, collection_name='exam_types') # reception exam, course exam, ...
    manager                 = db.ReferenceProperty(Person, collection_name='managed_exams')
    model_version           = db.StringProperty(default='A')


class ExamGroup(db.Model):
    exam                = db.ReferenceProperty(Exam, collection_name='exam_groups')
    first_entry_time    = db.DateTimeProperty()         # Time of first student entry
    last_entry_time     = db.DateTimeProperty()         # Time of last student entry
    group_size          = db.IntegerProperty()      # Number of students entering at the same time
    interval_minutes    = db.IntegerProperty()      # Interval between groups entering
    location            = db.ReferenceProperty(Location, collection_name='exam_groups')
    duration_minutes    = db.IntegerProperty()      # Estimated time student has to spend
    model_version       = db.StringProperty(default='A')


class ExamGroupRegistration(db.Model):
    exam_group      = db.ReferenceProperty(ExamGroup, collection_name='registrations')
    time            = db.TimeProperty()
    grade           = db.ReferenceProperty(Grade, collection_name='registrations')
    is_passed       = db.BooleanProperty()
    person          = db.ListProperty(db.Key) # Applicant and/or Person key.
    model_version   = db.StringProperty(default='A')