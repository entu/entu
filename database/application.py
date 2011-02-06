from google.appengine.ext import db

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
    communication_email     = db.StringProperty()
    is_published            = db.BooleanProperty(default=False)
    model_version           = db.StringProperty(default='A')


class Application(db.Model):
    reception               = db.ReferenceProperty(Reception, collection_name='applications')
    status                  = db.StringProperty(default='selected', choices=['selected', 'unselected', 'submitted'])
    comment                 = db.TextProperty()
    model_version           = db.StringProperty(default='A')


class ReceptionExam(db.Model):
    name                    = db.ReferenceProperty(Dictionary, collection_name='reception_exam_names')
    weight                  = db.IntegerProperty()
    is_milestone            = db.BooleanProperty()
    exam                    = db.ReferenceProperty(Exam, collection_name='receptions')
    reception               = db.ReferenceProperty(Reception, collection_name='exams')
    model_version           = db.StringProperty(default='A')