from google.appengine.ext import db
from google.appengine.ext import blobstore

from database.dictionary import *
from database.general import *
from database.person import *
from database.grade import *
from database.curriculum import *


# Application module
class Reception(db.Model):
    curriculum              = db.ReferenceProperty(Curriculum, collection_name='receptions')
    name                    = db.ReferenceProperty(Dictionary, collection_name='reception_names')
    description             = db.ReferenceProperty(Dictionary, collection_name='reception_descriptions')
    subsidized_places       = db.IntegerProperty()
    non_subsidized_places   = db.IntegerProperty()
    start_date              = db.DateProperty()
    end_date                = db.DateProperty()
    manager                 = db.ReferenceProperty(Person, collection_name='managed_receptions')
    is_published            = db.BooleanProperty(default=False)
    version                 = db.StringProperty(default='A')


class Applicant(db.Model):
    """
    There can be only single applicant for any person or document
    so "applicant" is used as back-reference instead of "applicants"
    """
    auto_id                 = db.IntegerProperty() # auto-increment
    forename                = db.StringProperty()
    surname                 = db.StringProperty()
    gender                  = db.ReferenceProperty(Dictionary, collection_name='applicant_genders')
    idcode                  = db.StringProperty() # isikukood
    birth_date              = db.DateProperty()
    photo                   = blobstore.BlobReferenceProperty()
    could_be_subsidised     = db.BooleanProperty(default=True)
    email                   = db.StringProperty()
    password                = db.StringProperty()
    person                  = db.ReferenceProperty(Person, collection_name='applicant')
    version                 = db.StringProperty(default='A')

    def documents():
        pass


class Application(db.Model):
    applicant               = db.ReferenceProperty(Applicant, collection_name='applications')
    reception               = db.ReferenceProperty(Reception, collection_name='applications')
    is_approved             = db.BooleanProperty() # can be set to true by department if documents are valid and application is approved
    version                 = db.StringProperty(default='A')


class ReceptionExam(db.Model):
    name                    = db.ReferenceProperty(Dictionary, collection_name='reception_exam_names')
    weight                  = db.IntegerProperty()
    is_milestone            = db.BooleanProperty()
    exam                    = db.ReferenceProperty(Exam, collection_name='receptions')
    reception               = db.ReferenceProperty(Reception, collection_name='exams')
    version                 = db.StringProperty(default='A')


class ReceptionExamGroupRegistration(db.Model):
    exam_group      = db.ReferenceProperty(ExamGroup, collection_name='reception_registrations')
    time            = db.TimeProperty()
    grade           = db.ReferenceProperty(GradeDefinition, collection_name='reception_registrations')
    is_passed       = db.BooleanProperty()
    applicant       = db.ReferenceProperty(Applicant, collection_name='exam_registrations')
    model_version   = db.StringProperty(default='A')