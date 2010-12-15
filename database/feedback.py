from google.appengine.ext import db
from datetime import date

from database import *


class Questionary(db.Model):
    name        = db.ReferenceProperty(Dictionary, collection_name='questionary_names')
    description = db.ReferenceProperty(Dictionary, collection_name='questionary_descriptions')
    start_date  = db.DateProperty()
    end_date    = db.DateProperty()
    is_template = db.BooleanProperty(default=False)
    manager     = db.ReferenceProperty(Person, collection_name='manager_of_questionaries')


class Question(db.Model):
    ordinal             = db.IntegerProperty(default=999);
    questionary         = db.ReferenceProperty(Questionary, collection_name='questions')
    name                = db.ReferenceProperty(Dictionary, collection_name='question_names')
    type                = db.StringProperty(choices=['like', 'rating', 'text'])
    is_mandatory        = db.BooleanProperty(default=False)
    is_teacher_specific = db.BooleanProperty(default=False)


class QuestionaryPerson(db.Model):
    questionary     = db.ReferenceProperty(Questionary, collection_name='questionary_persons')
    person          = db.ReferenceProperty(Person, collection_name='questionary_persons')
    course          = db.ReferenceProperty(Course, collection_name='questionary_persons')
    is_completed    = db.BooleanProperty(default=False)


class QuestionAnswer(db.Model):
    questionary_person  = db.ReferenceProperty(QuestionaryPerson, collection_name='answers')
    person              = db.ReferenceProperty(Person, collection_name='person_answers')
    target_person       = db.ReferenceProperty(Person, collection_name='target_person_answers')
    questionary         = db.ReferenceProperty(Questionary, collection_name='answers')
    course              = db.ReferenceProperty(Course, collection_name='questionary_answers')
    question            = db.ReferenceProperty(Question, collection_name='answers')
    question_string     = db.StringProperty()
    answer              = db.TextProperty()
    datetime            = db.DateTimeProperty()
    aggregation_date    = db.DateProperty(default=date(2000, 1, 1))