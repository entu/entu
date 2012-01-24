from google.appengine.ext import db
from datetime import date

from bo import *
from database.dictionary import *
from database.person import *
from database.bubble import *


class Questionary(ChangeLogModel):
    name            = db.ReferenceProperty(Dictionary, collection_name='questionary_names')
    description     = db.ReferenceProperty(Dictionary, collection_name='questionary_descriptions')
    start_date      = db.DateProperty()
    end_date        = db.DateProperty()
    manager         = db.ReferenceProperty(Person, collection_name='managed_questionaries')

    @property
    def displayname(self):
        return self.name.value

    @property
    def displaydate(self):
        if self.start_date and self.end_date:
            if self.start_date.strftime('%d.%m.%Y') == self.end_date.strftime('%d.%m.%Y'):
                return self.start_date.strftime('%d.%m.%Y')
            else:
                return self.start_date.strftime('%d.%m.%Y') + ' - ' + self.end_date.strftime('%d.%m.%Y')
        else:
            if self.start_date:
                return self.start_datetime.strftime('%d.%m.%Y') + ' - ...'
            else:
                return '... - ' + self.end_date.strftime('%d.%m.%Y')


class Question(ChangeLogModel):
    ordinal             = db.IntegerProperty(default=999);
    questionary         = db.ReferenceProperty(Questionary, collection_name='questions')
    name                = db.ReferenceProperty(Dictionary, collection_name='question_names')
    type                = db.StringProperty(choices=['like', 'rating', 'text'])
    is_mandatory        = db.BooleanProperty(default=False)
    is_teacher_specific = db.BooleanProperty(default=False)


class QuestionaryPerson(ChangeLogModel):
    questionary         = db.ReferenceProperty(Questionary, collection_name='questionary_persons')
    person              = db.ReferenceProperty(Person, collection_name='questionary_persons')
    person_b            = db.ReferenceProperty(Bubble, collection_name='questionary_persons_b')
    bubble              = db.ReferenceProperty(Bubble, collection_name='questionary_persons')
    is_completed        = db.BooleanProperty(default=False)
    is_obsolete         = db.BooleanProperty(default=False)


class QuestionAnswer(ChangeLogModel):
    questionary_person  = db.ReferenceProperty(QuestionaryPerson, collection_name='answers')
    person              = db.ReferenceProperty(Person, collection_name='person_answers')
    person_b            = db.ReferenceProperty(Bubble, collection_name='person_answers_b')
    target_person       = db.ReferenceProperty(Person, collection_name='target_person_answers')
    target_person_b     = db.ReferenceProperty(Bubble, collection_name='target_person_answers_b')
    questionary         = db.ReferenceProperty(Questionary, collection_name='answers')
    bubble              = db.ReferenceProperty(Bubble, collection_name='questionary_answers')
    question            = db.ReferenceProperty(Question, collection_name='answers')
    question_string     = db.StringProperty()
    answer              = db.TextProperty()
    datetime            = db.DateTimeProperty()
