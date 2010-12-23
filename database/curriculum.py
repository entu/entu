from google.appengine.ext import db

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
    version                 = db.StringProperty(default='A')


class Concentration(db.Model):
    name        = db.ReferenceProperty(Dictionary, collection_name='contcentrations')
    code        = db.StringProperty()
    tags        = db.StringListProperty()
    curriculum  = db.ReferenceProperty(Curriculum, collection_name='contcentrations')
    manager     = db.ReferenceProperty(Person, collection_name='managed_contcentrations')
    state       = db.StringProperty()
    version     = db.StringProperty(default='A')


class StudentConcentration(db.Model):
    student         = db.ReferenceProperty(Person, collection_name='contcentrations')
    contcentration  = db.ReferenceProperty(Concentration, collection_name='students')
    start_date      = db.DateProperty()
    end_date        = db.DateProperty()
    version         = db.StringProperty(default='A')


class Module(db.Model):
    name                    = db.ReferenceProperty(Dictionary, collection_name='modules')
    code                    = db.StringProperty()
    tags                    = db.StringListProperty()
    manager                 = db.ReferenceProperty(Person, collection_name='managed_modules')
    minimum_credit_points   = db.FloatProperty()
    minimum_subject_count   = db.IntegerProperty()
    state                   = db.StringProperty()
    version                 = db.StringProperty(default='A')


class Modulecontcentration(db.Model):
    is_mandatory    = db.BooleanProperty()
    module          = db.ReferenceProperty(Module, collection_name='contcentrations')
    contcentration  = db.ReferenceProperty(Concentration, collection_name='modules')
    version         = db.StringProperty(default='A')


class RatingScale(db.Model):
    name        = db.ReferenceProperty(Dictionary, collection_name='rating_scales')
    version     = db.StringProperty(default='A')


class GradeDefinition(db.Model):
    rating_scale    = db.ReferenceProperty(RatingScale, collection_name='grade_definitions')
    name            = db.ReferenceProperty(Dictionary, collection_name='grade_definition_names')
    is_positive     = db.BooleanProperty()
    equivalent      = db.IntegerProperty()
    version         = db.StringProperty(default='A')


class Subject(db.Model):
    name            = db.ReferenceProperty(Dictionary, collection_name='subject_names')
    code            = db.StringProperty()
    tags            = db.StringListProperty()
    credit_points   = db.FloatProperty()
    rating_scale    = db.ReferenceProperty(RatingScale, collection_name='subjects')
    manager         = db.ReferenceProperty(Person, collection_name='managed_subjects')
    state           = db.StringProperty()
    version         = db.StringProperty(default='A')


class PrerequisiteSubject(db.Model):
    prerequisite    = db.ReferenceProperty(Subject, collection_name='postrequisite')
    postrequisite   = db.ReferenceProperty(Subject, collection_name='prerequisite')
    version         = db.StringProperty(default='A')


class ModuleSubject(db.Model):
    is_mandatory    = db.BooleanProperty()
    module          = db.ReferenceProperty(Module, collection_name='subjects')
    subject         = db.ReferenceProperty(Subject, collection_name='modules')
    version         = db.StringProperty(default='A')


class Course(db.Model):
    subject                 = db.ReferenceProperty(Subject, collection_name='courses')
    subscription_open_date  = db.DateProperty()
    subscription_close_date = db.DateProperty()
    course_start_date       = db.DateProperty()
    course_end_date         = db.DateProperty()
    teachers                = db.ListProperty(db.Key)
    is_feedback_started     = db.BooleanProperty(default=False)
    version                 = db.StringProperty(default='A')


class Subscription(db.Model):
    student = db.ReferenceProperty(Person, collection_name='subscriptions')
    course  = db.ReferenceProperty(Course, collection_name='subscribers')
    grade   = db.ReferenceProperty(GradeDefinition, collection_name='subscriptions')
    version = db.StringProperty(default='A')