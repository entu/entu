from google.appengine.api import users
from google.appengine.ext import db

from bo import *
from database.zimport.zoin import *
from database.person import *


class zPerson(db.Model):
    user                = db.StringProperty() # forename.surname@domain
    forename            = db.StringProperty()
    surname             = db.StringProperty()
    idcode              = db.StringProperty()
    gender              = db.StringProperty()
    birth_date          = db.DateProperty()
    leecher             = db.TextProperty()
    seeder              = db.TextProperty()

    def zimport(self):
        p = GetZoin('Person', self.key().name())
        if not p:
            p = Person()

        if self.user:
            p.user = users.User(self.user)
        p.forename = self.forename
        p.surname = self.surname
        p.idcode = self.idcode
        p.gender = self.gender
        p.birth_date = self.birth_date
        p.leecher = GetZoinKeyList('Bubble', self.leecher)
        p.seeder = GetZoinKeyList('Bubble', self.seeder)
        p.put('zimport')

        AddZoin(
            entity_kind = 'Person',
            old_key = self.key().name(),
            new_key = p.key(),
        )

        self.delete()


class zRole(db.Model):
    name_estonian       = db.StringProperty()
    name_english        = db.StringProperty()
    rights              = db.StringProperty()
    template_name       = db.StringProperty()

    def zimport(self):
        r = GetZoin('Role', self.key().name())
        if not r:
            r = Role()

        name = Dictionary()
        name.name = 'role_name'
        name.estonian = self.name_estonian
        name.english = self.name_english

        r.name = name.add()
        r.rights = StrToList(self.rights)
        r.template_name = self.template_name
        r.put('zimport')

        AddZoin(
            entity_kind = 'Role',
            old_key = self.key().name(),
            new_key = r.key(),
        )

        self.delete()


class zPersonRole(db.Model):
    person              = db.StringProperty()
    role                = db.StringProperty()
    department          = db.StringProperty()

    def zimport(self):
        pr = GetZoin('PersonRole', self.key().name())
        if not pr:
            pr = PersonRole()

        pr.person = GetZoin('Person', self.person)
        pr.role = GetZoin('Role', self.role)
        pr.department = GetZoin('Department', self.department)
        pr.put('zimport')

        AddZoin(
            entity_kind = 'PersonRole',
            old_key = self.key().name(),
            new_key = pr.key(),
        )

        self.delete()





"""class zDepartment(db.Model):
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


class zPersonDocument(db.Model):
    person              = db.StringProperty()
    document            = db.StringProperty()
    relation            = db.StringProperty()
    date_time           = db.StringProperty()
    model_version       = db.StringProperty(default='A')"""