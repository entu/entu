from google.appengine.ext import db
from google.appengine.ext import search

from database.dictionary import *
from database.person import *


class Curriculum(db.Model):
    name                    = db.ReferenceProperty(Dictionary, collection_name='curriculum_names')
    department              = db.ReferenceProperty(Department, collection_name='curriculums')
    code                    = db.StringProperty()
    tags                    = db.StringListProperty()
    level_of_education      = db.ReferenceProperty(Dictionary, collection_name='curriculum_level_of_educations')
    form_of_training        = db.ReferenceProperty(Dictionary, collection_name='curriculum_form_of_trainings')
    nominal_years           = db.IntegerProperty()
    nominal_credit_points   = db.FloatProperty()
    degree                  = db.ReferenceProperty(Dictionary, collection_name='curriculum_degrees')
    manager                 = db.ReferenceProperty(Person, collection_name='managed_curriculums')
    state                   = db.StringProperty()


class Orientation(db.Model):
    name        = db.ReferenceProperty(Dictionary, collection_name='orientations')
    code        = db.StringProperty()
    tags        = db.StringListProperty()
    curriculum  = db.ReferenceProperty(Curriculum, collection_name='orientations')
    manager     = db.ReferenceProperty(Person, collection_name='managed_orientations')
    state       = db.StringProperty()


class StudentOrientation(db.Model):
    student     = db.ReferenceProperty(Person, collection_name='orientations')
    orientation = db.ReferenceProperty(Orientation, collection_name='students')
    start_date  = db.DateProperty()
    end_date    = db.DateProperty()


class Module(db.Model):
    name                    = db.ReferenceProperty(Dictionary, collection_name='modules')
    code                    = db.StringProperty()
    tags                    = db.StringListProperty()
    manager                 = db.ReferenceProperty(Person, collection_name='managed_modules')
    minimum_credit_points   = db.FloatProperty()
    minimum_subject_count   = db.IntegerProperty()
    state                   = db.StringProperty()


class ModuleOrientation(db.Model):
    is_mandatory    = db.BooleanProperty()
    module          = db.ReferenceProperty(Module, collection_name='orientations')
    orientation     = db.ReferenceProperty(Orientation, collection_name='modules')


class RatingScale(db.Model):
    name = db.ReferenceProperty(Dictionary, collection_name='rating_scales')


class GradeDefinition(db.Model):
    rating_scale    = db.ReferenceProperty(RatingScale, collection_name='grade_definitions')
    name            = db.ReferenceProperty(Dictionary, collection_name='grade_definition_names')
    is_positive     = db.BooleanProperty()
    equivalent      = db.IntegerProperty()


class Subject(db.Model):
    name            = db.ReferenceProperty(Dictionary, collection_name='subject_names')
    code            = db.StringProperty()
    tags            = db.StringListProperty()
    credit_points   = db.FloatProperty()
    rating_scale    = db.ReferenceProperty(RatingScale, collection_name='subjects')
    manager         = db.ReferenceProperty(Person, collection_name='managed_subjects')
    state           = db.StringProperty()


class PrerequisiteSubject(db.Model):
    prerequisite    = db.ReferenceProperty(Subject, collection_name='postrequisite')
    postrequisite   = db.ReferenceProperty(Subject, collection_name='prerequisite')


class ModuleSubject(db.Model):
    is_mandatory    = db.BooleanProperty()
    module          = db.ReferenceProperty(Module, collection_name='subjects')
    subject         = db.ReferenceProperty(Subject, collection_name='modules')


class Course(db.Model):
    subject                 = db.ReferenceProperty(Subject, collection_name='courses')
    subscription_open_date  = db.DateProperty()
    subscription_close_date = db.DateProperty()
    course_start_date       = db.DateProperty()
    course_end_date         = db.DateProperty()
    teachers                = db.ListProperty(db.Key)
    is_feedback_started     = db.BooleanProperty(default=False)


class Subscription(db.Model):
    student = db.ReferenceProperty(Person, collection_name='subscriptions')
    course  = db.ReferenceProperty(Course, collection_name='subscribers')
    grade   = db.ReferenceProperty(GradeDefinition, collection_name='subscriptions')