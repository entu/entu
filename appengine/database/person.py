from google.appengine.ext import db
from google.appengine.ext import search
from google.appengine.ext import blobstore
from google.appengine.api import images
from google.appengine.api import users
from google.appengine.api import taskqueue
from datetime import date
from datetime import datetime

from bo import *
from database.dictionary import *
from database.general import *
from libraries.gmemsess import *


class Role(ChangeLogModel):
    name            = db.ReferenceProperty(Dictionary, collection_name='role_names')
    rights          = db.StringListProperty()
    template_name   = db.StringProperty()
    model_version   = db.StringProperty(default='A')

    @property
    def displayname(self):
        if self.name:
            return self.name.translate()
        else:
            return ''


class Person(ChangeLogModel):
    #user                    = db.UserProperty()
    apps_username           = db.StringProperty() # forename.surname@domain
    email                   = db.StringProperty()
    password                = db.StringProperty()
    forename                = db.StringProperty()
    surname                 = db.StringProperty()
    idcode                  = db.StringProperty()
    gender                  = db.StringProperty(choices=['', 'male', 'female'])
    birth_date              = db.DateProperty()
    created                 = db.DateTimeProperty(auto_now_add=True)
    have_been_subsidised    = db.BooleanProperty(default=False)
    roles                   = db.ListProperty(db.Key)
    current_role            = db.ReferenceProperty(Role, collection_name='persons')
    last_seen               = db.DateTimeProperty()
    model_version           = db.StringProperty(default='A')
    seeder                  = db.ListProperty(db.Key)
    leecher                 = db.ListProperty(db.Key)
    search_names            = db.StringListProperty()


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
                name = self.primary_email
        return name

    @property
    def primary_email(self):
        if self.apps_username:
            return self.apps_username
        if self.emails:
            if len(self.emails) > 0:
                return self.emails[0]

    @property
    def emails(self):
        emails = []
        if self.email:
            emails = AddToList(self.email, emails)
        if self.apps_username:
            emails = AddToList(self.apps_username, emails)
        for contact in db.Query(Contact).ancestor(self).filter('type', 'email').fetch(1000):
            emails = AddToList(contact.value, emails)
        return emails

    @property
    def photo(self):
        return db.Query(Document).filter('types', 'person_photo').filter('entities', self.key()).get()

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
    def contacts(self):
        return db.Query(Contact).ancestor(self).fetch(1000)

    @property
    def Roles(self):
        return self.roles2()

    @property                   # TODO: refactor to Roles
    def roles2(self):
        if users.is_current_user_admin():
            return Role().all()

        if self.roles:
            return Role().get(self.roles)

    @property
    def current(self, web=None):
        user = users.get_current_user()
        if user:
            person = db.Query(Person).filter('apps_username', user.email()).get()
            if not person:
                person = Person()
                person.apps_username = user.email()
                person.idcode = 'guest'
                person.put()
            return person

    def current_s(self, web):
        if self.current:
            return self.current
        else:
            sess = Session(web, timeout=86400)
            if 'application_person_key' in sess:
                return Person().get(sess['application_person_key'])

    @property
    def changed(self):
        return datetime.today()
        date = self.last_change.datetime

        document = db.Query(Document).filter('entities', self.key()).filter('types', 'application_document').order('-created').get()
        if document:
            docs_date = document.created
            if docs_date > date:
                date = docs_date

        conversation = db.Query(Conversation).filter('entities', self.key()).filter('types', 'application').get()
        if conversation:
            message = db.Query(Message).ancestor(conversation).order('-created').get()
            if message:
                mess_date = message.created
                if mess_date > date:
                    date = mess_date

        return date

    def add_leecher(self, bubble_key):
        self.leecher = AddToList(bubble_key, self.leecher)
        self.put()
        taskqueue.Task(url='/taskqueue/bubble_change_leecher', params={'action': 'add', 'bubble_key': str(bubble_key), 'person_key': str(self.key())}).add(queue_name='bubble-one-by-one')

    def remove_leecher(self, bubble_key):
        self.leecher.remove(bubble_key)
        self.put()
        taskqueue.Task(url='/taskqueue/bubble_change_leecher', params={'action': 'remove', 'bubble_key': str(bubble_key), 'person_key': str(self.key())}).add(queue_name='bubble-one-by-one')

    def index_names(self):
        self.search_names = []
        if self.forename:
            forename = self.forename.lower()[:15]
            for i in range (1,len(forename)):
                self.search_names = AddToList(forename[:i], self.search_names)
        if self.surname:
            surname = self.surname.lower()[:15]
            for i in range (1,len(surname)):
                self.search_names = AddToList(surname[:i], self.search_names)
        if self.idcode:
            idcode = self.idcode.lower()[:15]
            for i in range (1,len(idcode)):
                self.search_names = AddToList(idcode[:i], self.search_names)


        self.put()


class Cv(ChangeLogModel): #parent=Person()
    type                = db.StringProperty(choices=['secondary_education', 'higher_education', 'workplace'])
    organisation        = db.StringProperty()
    start               = db.StringProperty()
    end                 = db.StringProperty()
    description         = db.StringProperty()
    model_version       = db.StringProperty(default='A')


class Department(ChangeLogModel):
    name                = db.ReferenceProperty(Dictionary, collection_name='department_names')
    is_academic         = db.BooleanProperty()
    parent_department   = db.SelfReferenceProperty(collection_name='child_departments')
    manager             = db.ReferenceProperty(Person, collection_name='managed_departments')
    model_version       = db.StringProperty(default='A')


class Contact(ChangeLogModel): #parent=Person()
    type                = db.StringProperty(choices=['email', 'phone', 'address', 'skype'])
    value               = db.StringProperty()
    model_version       = db.StringProperty(default='A')


class Document(ChangeLogModel):
    file            = blobstore.BlobReferenceProperty()
    external_link   = db.StringProperty()
    types           = db.StringListProperty()
    entities        = db.ListProperty(db.Key)
    title           = db.ReferenceProperty(Dictionary, collection_name='document_titles')
    content_type    = db.StringProperty()
    uploader        = db.ReferenceProperty(Person, collection_name='uploaded_documents')
    owners          = db.ListProperty(db.Key)
    editors         = db.ListProperty(db.Key)
    viewers         = db.ListProperty(db.Key)
    created         = db.DateTimeProperty(auto_now_add=True)
    visibility      = db.StringProperty(default='private', choices=['private', 'domain', 'public'])
    model_version   = db.StringProperty(default='A')

    @property
    def url(self):
        return '/document/' + str(self.key())


class Conversation(ChangeLogModel):
    types           = db.StringListProperty()
    entities        = db.ListProperty(db.Key)
    participants    = db.ListProperty(db.Key)
    created         = db.DateTimeProperty(auto_now_add=True)
    model_version   = db.StringProperty(default='A')

    def add_message(self, message, person = None):
        self.participants = AddToList(person, self.participants)
        self.put()

        mes = Message(parent=self)
        if person:
            mes.person = person
        mes.text = message
        mes.put()


class Message(ChangeLogModel): #parent=Conversation()
    person          = db.ReferenceProperty(Person, collection_name='messages')
    text            = db.TextProperty()
    created         = db.DateTimeProperty(auto_now_add=True)
    model_version   = db.StringProperty(default='A')
