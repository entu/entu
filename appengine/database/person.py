from google.appengine.ext import db
from google.appengine.ext import search
from google.appengine.ext import blobstore
from google.appengine.api import images
from google.appengine.api import users
from google.appengine.api import taskqueue
from datetime import date
from datetime import datetime

import hashlib

from bo import *
from database.dictionary import *
from libraries.gmemsess import *


class Role(ChangeLogModel):
    name            = db.ReferenceProperty(Dictionary, collection_name='role_names')
    rights          = db.StringListProperty()

    @property
    def displayname(self):
        if self.name:
            return self.name.value
        else:
            return ''


class Person(ChangeLogModel):
    is_guest                = db.BooleanProperty(default=False)
    users                   = db.StringListProperty()
    email                   = db.StringProperty()
    password                = db.StringProperty()
    forename                = db.StringProperty()
    surname                 = db.StringProperty()
    idcode                  = db.StringProperty()
    #citizenship             = db.StringProperty()
    #country_of_residence    = db.StringProperty()
    gender                  = db.StringProperty(choices=['', 'male', 'female'])
    birth_date              = db.DateProperty()
    #have_been_subsidised    = db.BooleanProperty(default=False)
    roles                   = db.ListProperty(db.Key)
    #current_role            = db.ReferenceProperty(Role, collection_name='persons')
    #last_seen               = db.DateTimeProperty()
    seeder                  = db.ListProperty(db.Key)
    leecher                 = db.ListProperty(db.Key)
    sort                    = db.StringProperty(default='')
    search                  = db.StringListProperty()
    merged_from             = db.ListProperty(db.Key)

    def AutoFix(self):
        if self.merged_from:
            l1 = ListUnique([str(k) for k in self.merged_from])
            l2 = ListUnique([str(k) for k in self.merged_from_all])
            if len(ListDiff(l1, l2))>0:
                self.merged_from = self.merged_from_all

        if self.forename:
            self.forename = self.forename.title().strip().replace('  ', ' ').replace('- ', '-').replace(' -', '-')

        if self.surname:
            self.surname = self.surname.title().strip().replace('  ', ' ').replace('- ', '-').replace(' -', '-')

        self.sort = StringToSortable(self.displayname)
        self.search = StringToSearchIndex(self.displayname)

        self.put('autofix')

    @property
    def displayname(self):
        name = ''
        if self.forename or self.surname:
            if self.forename:
                name = name + self.forename
            if self.surname:
                name = name + ' ' + self.surname
        else:
            if self.primary_email:
                name = self.primary_email.split('@')[0]
        return name

    @property
    def current(self):
        user = users.get_current_user()
        if user:
            # if user.email() == 'argoroots@gmail.com':
            #     return Person().get_by_id(5013376)
            person = db.Query(Person).filter('users', user.email()).filter('x_is_deleted', False).get()
            if not person:
                person = Person()
                person.users = [user.email()]
                person.is_guest = True
                person.put()
            return person

    @property
    def current_s(self):
        if self.current:
            return self.current
        else:
            sess = Session(web, timeout=86400)
            if 'application_person_key' in sess:
                return Person().get(sess['application_person_key'])

    @property
    def primary_email(self):
        if self.users:
            return self.users[0]
        emails = self.emails
        if len(emails) > 0:
            return emails[0]

    @property
    def emails(self):
        emails = []
        if self.users:
            emails = ListMerge(self.users[0], emails)
        if self.email:
            emails = ListMerge(self.email, emails)
        for contact in db.Query(Contact).ancestor(self).filter('type', 'email').fetch(1000):
            emails = ListMerge(contact.value, emails)
        return emails

    @property
    def photo(self):
        pass

    @property
    def age(self):
        if self.birth_date:
            today = date.today()
            try: # raised when birth date is February 29 and the current year is not a leap year
                birthday = self.birth_date.replace(year=today.year)
            except ValueError:
                birthday = self.birth_date.replace(year=today.year, day=self.birth_date.day-1)
            if birthday > today:
                return today.year - self.birth_date.year - 1
            else:
                return today.year - self.birth_date.year

    @property
    def merged_from_all(self):
        result = []
        if self.merged_from:
            result = self.merged_from
            for pk in self.merged_from:
                p = Person().get(pk)
                result = ListMerge(result, p.merged_from_all)
        return ListUnique(result)

    @property
    def merged_to(self):
        return ListUnique(db.Query(Person, keys_only=True).filter('merged_from', self.key()))

    def GetPhotoUrl(self, size = ''):
        email = self.primary_email if self.primary_email else self.displayname
        return 'http://www.gravatar.com/avatar/%s?s=%s&d=monsterid' % (hashlib.md5(email.encode('utf-8').strip().lower()).hexdigest(), size)

    def GetContacts(self):
        return db.Query(Contact).ancestor(self).filter('_is_deleted', False).filter('type != ', 'email').fetch(1000)

    def GetRoles(self):
        if users.is_current_user_admin():
            return Role().all()
        if self.roles:
            return Role().get(self.roles)

    def AddLeecher(self, bubble_key):
        self.leecher = ListMerge(bubble_key, self.leecher)
        self.put()
        taskqueue.Task(url='/taskqueue/bubble_change_leecher', params={'action': 'add', 'bubble_key': str(bubble_key), 'person_key': str(self.key())}).add(queue_name='bubble-one-by-one')

    def RemoveLeecher(self, bubble_key):
        self.leecher.remove(bubble_key)
        self.put()
        taskqueue.Task(url='/taskqueue/bubble_change_leecher', params={'action': 'remove', 'bubble_key': str(bubble_key), 'person_key': str(self.key())}).add(queue_name='bubble-one-by-one')


class Cv(ChangeLogModel):
    person          = db.ReferenceProperty(Person, collection_name='cv')
    type            = db.StringProperty(choices=['secondary_education', 'higher_education', 'workplace'])
    organisation    = db.StringProperty()
    start           = db.StringProperty()
    end             = db.StringProperty()
    description     = db.StringProperty()


class Contact(ChangeLogModel):
    person          = db.ReferenceProperty(Person, collection_name='contacts')
    type            = db.StringProperty(choices=['email', 'phone', 'address', 'skype'])
    value           = db.StringProperty()

    def AutoFix(self):
        if self.type == 'phone':
            self.value = self.value.strip().replace(' ', '').replace('+372', '')

        if self.type == 'email':
            self.value = self.value.strip().replace(' ', '')

        if self.type == 'skype':
            self.value = self.value.strip().replace(' ', '')

        if self.value.strip():
            self._is_deleted = False
        else:
            self._is_deleted = True

        if self.type == 'email' and (len(self.value) < 5 or self.value.find('@') == -1):
            self._is_deleted = True

        if self.type == 'phone' and len(self.value) < 7:
            self._is_deleted = True

        self.put('autofix')


class Conversation(ChangeLogModel):
    types           = db.StringListProperty()
    entities        = db.ListProperty(db.Key)
    participants    = db.ListProperty(db.Key)

    def AddMessage(self, message, person = None):
        self.participants = ListMerge(person, self.participants)
        self.put()

        mes = Message(parent=self)
        if person:
            mes.person = person
        mes.text = message
        mes.put()


class Message(ChangeLogModel): #parent=Conversation()
    person          = db.ReferenceProperty(Person, collection_name='messages')
    text            = db.TextProperty()
