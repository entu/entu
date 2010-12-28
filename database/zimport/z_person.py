from google.appengine.ext import db

from database.import.zoin import *



class zPerson(db.Model):
    apps_username       = db.StringProperty() # forename.surname@domain
    forename            = db.StringProperty()
    surname             = db.StringProperty()
    idcode              = db.StringProperty()
    gender_estonian     = db.StringProperty()
    gender_english      = db.StringProperty()
    birth_date          = db.StringProperty()

    def Import(self):
        return ' '.join([self.forename, self.surname])




class zDepartment(db.Model):
    name                = db.StringProperty()
    is_academic         = db.StringProperty()
    parent_department   = db.StringProperty()
    manager             = db.StringProperty()
    model_version       = db.StringProperty(default='A')


class zContact(db.Model):
    person              = db.StringProperty()
    type                = db.StringProperty()
    value               = db.StringProperty()
    model_version       = db.StringProperty(default='A')


class zRole(db.Model):
    name                = db.StringProperty()
    rights              = db.StringProperty()
    model_version       = db.StringProperty(default='A')


class zPersonRole(db.Model):
    person              = db.StringProperty()
    role                = db.StringProperty()
    department          = db.StringProperty()
    model_version       = db.StringProperty(default='A')


class zPersonDocument(db.Model):
    person              = db.StringProperty()
    document            = db.StringProperty()
    relation            = db.StringProperty()
    date_time           = db.StringProperty()
    model_version       = db.StringProperty(default='A')