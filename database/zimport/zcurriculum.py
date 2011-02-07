from google.appengine.ext import db

from database.zimport.zoin import *
from database.curriculum import *


class zCurriculum(db.Model):
    name_estonian               = db.StringProperty()
    name_english                = db.StringProperty()
    code                        = db.StringProperty()
    tag                         = db.StringProperty()
    level_of_education_estonian = db.StringProperty()
    level_of_education_english  = db.StringProperty()
    form_of_training_estonian   = db.StringProperty()
    form_of_training_english    = db.StringProperty()
    nominal_years               = db.IntegerProperty()
    nominal_credit_points       = db.FloatProperty()
    degree_estonian             = db.StringProperty()
    degree_english              = db.StringProperty()
    state                       = db.StringProperty()

    def zimport(self):
        c = GetZoin('Curriculum', self.key().name())
        if not c:
            c = Curriculum()

        name = Dictionary()
        name.name = 'curriculum_name'
        name.estonian = self.name_estonian
        name.english = self.name_english

        level_of_education = Dictionary()
        level_of_education.name = 'curriculum_level_of_education'
        level_of_education.estonian = self.level_of_education_estonian
        level_of_education.english = self.level_of_education_english

        form_of_training = Dictionary()
        form_of_training.name = 'curriculum_form_of_training'
        form_of_training.estonian = self.form_of_training_estonian
        form_of_training.english = self.form_of_training_english

        degree = Dictionary()
        degree.name = 'curriculum_degree'
        degree.estonian = self.degree_estonian
        degree.english = self.degree_english

        c.name = name.add()
        c.code = self.code
        c.tags = [self.tag]
        c.level_of_education = level_of_education.add()
        c.form_of_training = form_of_training.add()
        c.nominal_years = self.nominal_years
        c.nominal_credit_points = self.nominal_credit_points
        c.degree = degree.add()
        c.state = self.state

        c.put()

        AddZoin(
            entity_kind = 'Curriculum',
            old_key = self.key().name(),
            new_key = c.key(),
        )

        self.delete()


"""class zConcentration(db.Model):
    name            = db.ReferenceProperty(Dictionary, collection_name='concentration_names')
    code            = db.StringProperty()
    tags            = db.StringListProperty()
    curriculum      = db.ReferenceProperty(Curriculum, collection_name='concentrations')
    manager         = db.ReferenceProperty(Person, collection_name='managed_concentrations')
    state           = db.StringProperty(choices=['current', 'obsolete', 'archived'], default='current')


class zStudentConcentration(db.Model):
    student         = db.ReferenceProperty(Person, collection_name='student_concentrations')
    concentration   = db.ReferenceProperty(Concentration, collection_name='students')
    start_date      = db.DateProperty()
    end_date        = db.DateProperty()


class zModule(db.Model):
    name                    = db.ReferenceProperty(Dictionary, collection_name='module_names')
    code                    = db.StringProperty()
    tags                    = db.StringListProperty()
    manager                 = db.ReferenceProperty(Person, collection_name='managed_modules')
    minimum_credit_points   = db.FloatProperty(default=0.0) # Minimum amount of credit points student has to earn in this module. Defaults to 0
    minimum_subject_count   = db.IntegerProperty(default=0) # Minimum number of subjects student has to pass in this module. Defaults to 0
    state                   = db.StringProperty(choices=['current', 'obsolete', 'archived'], default='current')
    model_version           = db.StringProperty(default='A')


class zModuleConcentration(db.Model):
    is_mandatory    = db.BooleanProperty()
    module          = db.ReferenceProperty(Module, collection_name='concentrations')
    concentration   = db.ReferenceProperty(Concentration, collection_name='modules')
    model_version   = db.StringProperty(default='A')


class zSubject(db.Model):
    name            = db.ReferenceProperty(Dictionary, collection_name='subject_names')
    code            = db.StringProperty()
    tags            = db.StringListProperty()
    credit_points   = db.FloatProperty()
    rating_scale    = db.ReferenceProperty(RatingScale, collection_name='subjects')
    manager         = db.ReferenceProperty(Person, collection_name='managed_subjects')
    state           = db.StringProperty(choices=['current', 'obsolete', 'archived'], default='current')
    model_version   = db.StringProperty(default='A')


class zPrerequisiteSubject(db.Model):
    prerequisite    = db.ReferenceProperty(Subject, collection_name='postrequisites')
    postrequisite   = db.ReferenceProperty(Subject, collection_name='prerequisites')
    model_version   = db.StringProperty(default='A')


class zModuleSubject(db.Model):
    is_mandatory    = db.BooleanProperty() # Subject could be marked mandatory to pass the module
    module          = db.ReferenceProperty(Module, collection_name='subjects')
    subject         = db.ReferenceProperty(Subject, collection_name='modules')
    model_version   = db.StringProperty(default='A')


class zCourse(db.Model):
    subject                 = db.ReferenceProperty(Subject, collection_name='courses')
    subscription_open_date  = db.DateProperty()
    subscription_close_date = db.DateProperty()
    course_start_date       = db.DateProperty()
    course_end_date         = db.DateProperty()
    teachers                = db.ListProperty(db.Key) # References to persons
    is_feedback_started     = db.BooleanProperty(default=False)
    model_version           = db.StringProperty(default='A')


class zSubscription(db.Model):
    student         = db.ReferenceProperty(Person, collection_name='subscribed_courses')
    course          = db.ReferenceProperty(Course, collection_name='subscriptions')
    grade           = db.ReferenceProperty(GradeDefinition, collection_name='subscriptions')
    model_version   = db.StringProperty(default='A')


class zCourseExam(db.Model):
    name            = db.ReferenceProperty(Dictionary, collection_name='course_exam_names') # usually "Scheduled", could be set to "Extraordinary" or any other arbitrary name
    course          = db.ReferenceProperty(Course, collection_name='exams')
    exam            = db.ReferenceProperty(Exam, collection_name='courses')
    model_version   = db.StringProperty(default='A')"""