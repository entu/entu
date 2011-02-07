from google.appengine.ext import db

from database.zimport.zoin import *
from database.application import *


class zReception(db.Model):
    curriculum              = db.StringProperty()
    name_estonian           = db.StringProperty()
    name_english            = db.StringProperty()
    description_estonian    = db.StringProperty(multiline=True)
    description_english     = db.StringProperty(multiline=True)
    subsidized_places       = db.IntegerProperty()
    non_subsidized_places   = db.IntegerProperty()
    start_date              = db.DateProperty()
    end_date                = db.DateProperty()
    manager                 = db.StringProperty()
    communication_email     = db.StringProperty()
    is_published            = db.BooleanProperty()

    def zimport(self):
        r = GetZoin('Reception', self.key().name())
        if not r:
            r = Reception()

        name = Dictionary()
        name.name = 'reception_name'
        name.estonian = self.name_estonian
        name.english = self.name_english

        description = Dictionary()
        description.name = 'reception_description'
        description.estonian = self.description_estonian
        description.english = self.description_english

        curriculum = GetZoin('Curriculum', self.curriculum)
        manager = GetZoin('Person', self.manager)

        r.curriculum = curriculum
        r.name = name.add()
        r.description = description.add()
        r.subsidized_places = self.subsidized_places
        r.start_date = self.start_date
        r.end_date = self.end_date
        r.manager = manager
        r.communication_email = self.communication_email
        r.is_published = self.is_published

        r.put()

        AddZoin(
            entity_kind = 'Reception',
            old_key = self.key().name(),
            new_key = r.key(),
        )

        self.delete()



class zReceptionExam(db.Model):
    #name                    = db.ReferenceProperty(Dictionary, collection_name='reception_exam_names')
    weight                  = db.IntegerProperty()
    is_milestone            = db.BooleanProperty()
    #exam                    = db.ReferenceProperty(Exam, collection_name='receptions')
    #reception               = db.ReferenceProperty(Reception, collection_name='exams')