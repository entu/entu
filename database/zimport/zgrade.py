from google.appengine.ext import db

from database.zimport.zoin import *
from database.grade import *


"""class zGrade(db.Model):
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


class zRatingScale(db.Model):
    name            = db.ReferenceProperty(Dictionary, collection_name='rating_scale_names')
    model_version   = db.StringProperty(default='A')


class zGradeDefinition(db.Model):
    rating_scale    = db.ReferenceProperty(RatingScale, collection_name='grade_definitions')
    name            = db.ReferenceProperty(Dictionary, collection_name='grade_definition_names')
    is_positive     = db.BooleanProperty()
    equivalent      = db.IntegerProperty()
    model_version   = db.StringProperty(default='A')"""


class zExam(db.Model):
    name_estonian           = db.StringProperty()
    name_english            = db.StringProperty()
    description_estonian    = db.StringProperty(multiline=True)
    description_english     = db.StringProperty(multiline=True)
    examiner                = db.StringProperty()
    registration_start_date = db.DateProperty()
    rankings_date           = db.DateProperty()
    type                    = db.StringProperty()
    manager                 = db.StringProperty()
    rating_scale            = db.StringProperty()

    def zimport(self):
        e = GetZoin('Exam', self.key().name())
        if not e:
            e = Exam()

        name = Dictionary()
        name.name = 'exam_name'
        name.estonian = self.name_estonian
        name.english = self.name_english

        description = Dictionary()
        description.name = 'reception_description'
        description.estonian = self.description_estonian
        description.english = self.description_english

        examiner = GetZoin('Person', self.examiner)
        manager = GetZoin('Person', self.manager)

        e.name = name.add()
        e.description = description.add()
        e.examiner = examiner
        e.registration_start_date = self.registration_start_date
        e.rankings_date = self.rankings_date
        e.type = self.type
        e.manager = manager
        e.rating_scale = self.rating_scale
        e.put()

        AddZoin(
            entity_kind = 'Exam',
            old_key = self.key().name(),
            new_key = e.key(),
        )

        self.delete()


"""class zExamGroup(db.Model):
    exam                = db.ReferenceProperty(Exam, collection_name='exam_groups')
    first_entry_time    = db.DateTimeProperty()         # Time of first student entry
    last_entry_time     = db.DateTimeProperty()         # Time of last student entry
    group_size          = db.IntegerProperty()      # Number of students entering at the same time
    interval_minutes    = db.IntegerProperty()      # Interval between groups entering
    location            = db.ReferenceProperty(Location, collection_name='exam_groups')
    duration_minutes    = db.IntegerProperty()      # Estimated time student has to spend
    model_version       = db.StringProperty(default='A')


class zExamGroupRegistration(db.Model):
    exam_group      = db.ReferenceProperty(ExamGroup, collection_name='registrations')
    time            = db.TimeProperty()
    grade           = db.ReferenceProperty(Grade, collection_name='registrations')
    is_passed       = db.BooleanProperty()
    person          = db.ListProperty(db.Key) # Applicant and/or Person key.
    model_version   = db.StringProperty(default='A')"""