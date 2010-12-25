from google.appengine.ext import db

from database.dictionary import *
from database.general import *
from database.person import *
from database.grade import *


class Curriculum(db.Model):
    name                    = db.ReferenceProperty(Dictionary, collection_name='curriculum_names')
    department              = db.ReferenceProperty(Department, collection_name='curriculums')
    code                    = db.StringProperty()           """ It is common in Learning Systems to give a code for almost everything. This makes it easy to perform searches and also these codes are commonly used in communication. """
    tags                    = db.StringListProperty()       """ Sometimes there is a need to change a “code”. Reason could be internal academic restructuring or it might be requirement from government. On such case the previous code will be stored in tags list so curriculum will remain findable by old code. """
    level_of_education      = db.ReferenceProperty(Dictionary, collection_name='curriculum_level_of_educations')
    form_of_training        = db.ReferenceProperty(Dictionary, collection_name='curriculum_form_of_trainings')
    nominal_years           = db.IntegerProperty()
    nominal_credit_points   = db.FloatProperty()
    degree                  = db.ReferenceProperty(Dictionary, collection_name='curriculum_degrees')
    manager                 = db.ReferenceProperty(Person, collection_name='managed_curriculums')
    state                   = db.StringProperty()           """ One of following:
                current  - New relations can be created, searchable;
                obsolete - No new relations are accepted, searchable;
                archived - No new relations are accepted, searchable only with archive search. """
    model_version           = db.StringProperty(default='A')


class Concentration(db.Model):
    name            = db.ReferenceProperty(Dictionary, collection_name='concentration_names')
    code            = db.StringProperty()
    tags            = db.StringListProperty()
    curriculum      = db.ReferenceProperty(Curriculum, collection_name='concentrations')
    manager         = db.ReferenceProperty(Person, collection_name='managed_concentrations')
    state           = db.StringProperty()                   # Valid states are current/obsolete/archived.
    model_version   = db.StringProperty(default='A')


class StudentConcentration(db.Model):
    student         = db.ReferenceProperty(Person, collection_name='student_concentrations')
    concentration   = db.ReferenceProperty(Concentration, collection_name='students')
    start_date      = db.DateProperty()
    end_date        = db.DateProperty()
    model_version   = db.StringProperty(default='A')


class Module(db.Model):
    name                    = db.ReferenceProperty(Dictionary, collection_name='modules')
    code                    = db.StringProperty()
    tags                    = db.StringListProperty()
    manager                 = db.ReferenceProperty(Person, collection_name='managed_modules')
    minimum_credit_points   = db.FloatProperty(default=0)   # Minimum amount of credit points student has to earn in this module. Defaults to 0
    minimum_subject_count   = db.IntegerProperty(default=0) # Minimum number of subjects student has to pass in this module. Defaults to 0
    state                   = db.StringProperty()           # Valid states are current/obsolete/archived.
    model_version           = db.StringProperty(default='A')


class ModuleConcentration(db.Model):
    is_mandatory    = db.BooleanProperty()  """ If module is set mandatory in concentration
                                               and student has subscribed to concentration
                                              then student has to satisfy minimum requirements in Module. """
    module          = db.ReferenceProperty(Module, collection_name='concentrations')
    concentration   = db.ReferenceProperty(Concentration, collection_name='modules')
    model_version   = db.StringProperty(default='A')


class Subject(db.Model):
    name            = db.ReferenceProperty(Dictionary, collection_name='subject_names')
    code            = db.StringProperty()
    tags            = db.StringListProperty()
    credit_points   = db.FloatProperty()
    rating_scale    = db.ReferenceProperty(RatingScale, collection_name='subjects')
    manager         = db.ReferenceProperty(Person, collection_name='managed_subjects')
    state           = db.StringProperty()                   # Valid states are current/obsolete/archived.
    model_version   = db.StringProperty(default='A')


class PrerequisiteSubject(db.Model):
    prerequisite    = db.ReferenceProperty(Subject, collection_name='postrequisites')
    postrequisite   = db.ReferenceProperty(Subject, collection_name='prerequisites')
    model_version   = db.StringProperty(default='A')


class ModuleSubject(db.Model):
    is_mandatory    = db.BooleanProperty()  # Subject could be marked mandatory to pass the module
    module          = db.ReferenceProperty(Module, collection_name='subjects')
    subject         = db.ReferenceProperty(Subject, collection_name='modules')
    model_version   = db.StringProperty(default='A')


class Course(db.Model):
    subject                 = db.ReferenceProperty(Subject, collection_name='courses')
    subscription_open_date  = db.DateProperty()
    subscription_close_date = db.DateProperty()
    course_start_date       = db.DateProperty()
    course_end_date         = db.DateProperty()
    teachers                = db.ListProperty(db.Key)       # References to persons
    is_feedback_started     = db.BooleanProperty(default=False)
    model_version           = db.StringProperty(default='A')


class Subscription(db.Model):
    student         = db.ReferenceProperty(Person, collection_name='subscribed_courses')
    course          = db.ReferenceProperty(Course, collection_name='subscriptions')
    grade           = db.ReferenceProperty(GradeDefinition, collection_name='subscriptions')
    model_version   = db.StringProperty(default='A')


class CourseExam(db.Model):
    name            = db.ReferenceProperty(Dictionary, collection_name='course_exam_names') """
                    usually "Scheduled", could be set to "Extraordinary" or any other arbitrary name"""
    course          = db.ReferenceProperty(Course, collection_name='exams')
    exam            = db.ReferenceProperty(Exam, collection_name='courses')
    model_version   = db.StringProperty(default='A')


class CourseExamGroupRegistration(db.Model):
    exam_group      = db.ReferenceProperty(ExamGroup, collection_name='course_registrations')
    time            = db.TimeProperty()
    grade           = db.ReferenceProperty(GradeDefinition, collection_name='course_registrations')
    is_passed       = db.BooleanProperty()
    student         = db.ReferenceProperty(Person, collection_name='exam_registrations')
    model_version   = db.StringProperty(default='A')