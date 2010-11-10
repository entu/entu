from google.appengine.ext import db

from database import *


class Questionary(db.Model):
    name        = db.ReferenceProperty(Dictionary, collection_name='questionary_names')
    description = db.ReferenceProperty(Dictionary, collection_name='questionary_descriptions')
    start_date  = db.DateProperty()
    end_date    = db.DateProperty()
    #related_entities
    #is_template
    manager     = db.ReferenceProperty(Person, collection_name='manager_of_questionaries')


class Question(db.Model):
    questionary         = db.ReferenceProperty(Questionary, collection_name='questions')
    name                = db.ReferenceProperty(Dictionary, collection_name='questions')
    type                = db.StringProperty(choices=['freetext', 'lickert'])
    is_mandatory        = db.BooleanProperty(default=False)
    is_teacher_specific = db.BooleanProperty(default=False)


class QuestionaryPerson(db.Model):
    questionary     = db.ReferenceProperty(Questionary, collection_name='questionary_persons')
    person          = db.ReferenceProperty(Person, collection_name='questionary_person')
    is_completed    = db.BooleanProperty(default=False)
    course          = db.ReferenceProperty(Course, collection_name='questionary_persons')


class QuestionAnswer(db.Model):
    question            = db.ReferenceProperty(Question, collection_name='question_answers')
    question_string     = db.StringProperty()
    questionary_person  = db.ReferenceProperty(QuestionaryPerson, collection_name='questionary_answers')
    answer              = db.StringProperty()
    datetime            = db.DateTimeProperty()
    teacher             = db.ReferenceProperty(Person, collection_name='teacher_answers')
    is_mandatory        = db.BooleanProperty()