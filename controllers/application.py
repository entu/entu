from google.appengine.api import users
from django.utils import simplejson
import datetime
import random
import string

from bo import *
from database.application import *
from database.person import *
from database.zimport.zgeneral import *
from libraries.gmemsess import *


class ShowSignin(boRequestHandler):
    def get(self):

        user = users.get_current_user()
        if user:
            self.redirect(users.create_logout_url('/application/signin'))

        sess = Session(self, timeout=86400)
        sess.invalidate()

        self.view('application', 'application/signup.html', {
            'account_login_url': users.create_login_url('/application'),
        })

    def post(self):

        email = self.request.get('email').strip()
        password = self.request.get('applicant_pass').strip()

        if email:
            p = db.Query(Person).filter('email', email).get()
            if not p:
                p = db.Query(Person).filter('apps_username', email).get()
                if not p:
                    p = Person()
                    p.email = email
                    p.idcode = ''
                    p.model_version = 'SSS'
                    p.put()

                    c = Contact(parent=p)
                    c.type = 'email'
                    c.value = email
                    c.put()

                    con = db.Query(Conversation).filter('entities', p.key()).filter('types', 'application').get()
                    if not con:
                        con = Conversation()
                        con.types = ['application']
                        con.entities = [p.key()]
                    con.participants = AddToList(p.key(), con.participants)
                    con.put()

                    mes = Message(parent=con)
                    mes.text = Translate('application_newuser_log_message') % email
                    mes.put()


            password = ''.join(random.choice(string.ascii_letters) for x in range(2))
            password += str(p.key().id())
            password += ''.join(random.choice(string.ascii_letters) for x in range(3))
            password = password.replace('O', random.choice(string.ascii_lowercase))

            p.password = password
            p.put()

            if SendMail(
                to = email,
                subject = Translate('application_signup_mail_subject'),
                message = Translate('application_signup_mail_message') % p.password
            ):
                self.response.out.write('OK')

        else:
            if password:
                p = db.Query(Person).filter('password', password).get()
                if p:
                    sess = Session(self, timeout=86400)
                    sess['application_person_key'] = p.key()
                    sess.save()
                    self.response.out.write('OK')


class ShowApplication(boRequestHandler):
    def get(self, url):
        p =  Person().current_s(self)
        if not p:
            self.redirect('/application/signin')
        else:
            now = datetime.now()
            receptions = []
            application_statuses = []
            for a in db.Query(Application).ancestor(p).fetch(1000):
                receptions.append({'reception': a.reception, 'application': a})
                application_statuses = AddToList(a.status, application_statuses)

            application_status = 'unselected'
            application_readonly = False
            if 'selected' in application_statuses:
                application_status = 'selected'
            if 'submitted' in application_statuses:
                application_status = 'submitted'
                application_readonly = True
            if 'accepted' in application_statuses:
                application_status = 'accepted'
                application_readonly = True

            photo_upload_url = blobstore.create_upload_url('/document/upload')
            document_upload_url = blobstore.create_upload_url('/document/upload')
            documents = db.Query(Document).filter('entities', p.key()).filter('types', 'application_document').fetch(1000)
            secondaryschools = db.Query(Cv).ancestor(p).filter('type', 'secondary_education').fetch(1000)
            highschools = db.Query(Cv).ancestor(p).filter('type', 'higher_education').fetch(1000)
            workplaces = db.Query(Cv).ancestor(p).filter('type', 'workplace').fetch(1000)

            conversation = db.Query(Conversation).filter('entities', p.key()).filter('types', 'application').get()
            if conversation:
                messages = db.Query(Message).ancestor(conversation).fetch(1000)
                for message in messages:
                    message.created = UtcToLocalDateTime(message.created)
            else:
                messages = {}

            self.view('application', 'application/application.html', {
                'post_url': '/application',
                'application_status': application_status,
                'application_readonly': application_readonly,
                'receptions': receptions,
                'person': p,
                'date_days': range(1, 32),
                'date_months': Translate('list_months').split(','),
                'document_types': Translate('application_documents_types').split(','),
                'date_years': range((now.year-15), (now.year-90), -1),
                'photo_upload_url': photo_upload_url,
                'document_upload_url': document_upload_url,
                'documents': documents,
                'secondaryschools': secondaryschools,
                'highschools': highschools,
                'workplaces': workplaces,
                'messages': messages,
            })

    def post(self, url):
        p =  Person().current_s(self)
        if p:
            key = self.request.get('key').strip()
            field = self.request.get('field').strip()
            value = self.request.get('value').strip()
            respond = {}

            r = Reception().get(key)
            if r:
                a = db.Query(Application).ancestor(p).filter('reception', r).get()
                if not a:
                    a = Application(parent=p)
                    a.reception = r

                if field == 'selected':
                    if value.lower() == 'true':
                        a.status = 'selected'
                    else:
                        a.status = 'unselected'

                if field == 'comment':
                    a.comment = value

                a.put()

            respond['key'] = key
            self.response.out.write(simplejson.dumps(respond))


class SubmitApplication(boRequestHandler):
    def get(self):
        p =  Person().current_s(self)
        if p:
            selected = False
            for a in db.Query(Application).ancestor(p).filter('status', 'selected').fetch(1000):
                a.status = 'submitted'
                a.put()
                selected = True
                SendMail(
                    to = a.reception.communication_email,
                    subject = Translate('application_submit_email1_subject') % p.displayname,
                    message = Translate('application_submit_email1_message') % {'name': p.displayname, 'link': SYSTEM_URL + '/reception/application/' + str(p.key()) }
                )

            if selected:

                con = db.Query(Conversation).filter('entities', p.key()).filter('types', 'application').get()
                if not con:
                    con = Conversation()
                    con.types = ['application']
                    con.entities = [p.key()]
                con.participants = AddToList(p.key(), con.participants)
                con.put()

                mes = Message(parent=con)
                mes.text = Translate('application_submit_log_message')
                mes.person = p
                mes.put()

                emails = []
                if p.email:
                    emails = AddToList(p.email, emails)
                if p.apps_username:
                    emails = AddToList(p.apps_username, emails)
                for contact in db.Query(Contact).ancestor(p).filter('type', 'email').fetch(1000):
                    emails = AddToList(contact.value, emails)

                SendMail(
                    to = emails,
                    subject = Translate('application_submit_email2_subject') % p.displayname,
                    message = Translate('application_submit_email2_message')
                )

                sess = Session(self, timeout=86400)
                sess.invalidate()
                self.redirect(users.create_logout_url('/application/thanks'))

            else:
                self.redirect('/application')
                return


class ShowSubmitApplication(boRequestHandler):
    def get(self):
        self.view('application', 'application/submitted.html', {
            'message': Translate('application_submit_success_message')
        })


class EditPerson(boRequestHandler):
    def post(self):
        p =  Person().current_s(self)
        if p:
            field = self.request.get('field').strip()
            value = self.request.get('value').strip()
            respond = {}

            if field in ['forename', 'surname', 'idcode', 'gender']:
                setattr(p, field, value)

            if field == 'birthdate':
                if value:
                    p.birth_date = datetime.strptime(value, '%d.%m.%Y').date()
                else:
                    p.birth_date = None

            if field == 'have_been_subsidised':
                if value.lower() == 'true':
                    p.have_been_subsidised = True
                else:
                    p.have_been_subsidised = False

            p.put()
            self.response.out.write(simplejson.dumps(respond))


class EditContact(boRequestHandler):
    def post(self):
        p =  Person().current_s(self)
        if p:
            key = self.request.get('key').strip()
            type = self.request.get('type').strip()
            value = self.request.get('value').strip()
            respond = {}

            if key:
                c = Contact().get(key)
                if value:
                    c.type = type
                    c.value = value
                    c.put()
                    response_key = str(c.key())
                else:
                    c.delete()
                    response_key = ''
            else:
                c = Contact(parent=p)
                c.type = type
                c.value = value
                c.put()
                response_key = str(c.key())

            respond['key'] = response_key

            p.put()
            self.response.out.write(simplejson.dumps(respond))


class EditCV(boRequestHandler):
    def post(self):
        p =  Person().current_s(self)
        if p:
            key = self.request.get('key').strip()
            field = self.request.get('field').strip()
            value = self.request.get('value').strip()
            type = self.request.get('type').strip()
            respond = {}

            if key:
                cv = Cv().get(key)
            else:
                cv = Cv(parent=p)
                cv.type = type

            if field in ['organisation','start', 'end', 'description']:
                setattr(cv, field, value)

            cv.put()
            respond['key'] = str(cv.key())

            self.response.out.write(simplejson.dumps(respond))


class PostMessage(boRequestHandler):
    def post(self):
        p =  Person().current_s(self)
        if p:
            message = self.request.get('message').strip()
            respond = {}

            if message:
                con = db.Query(Conversation).filter('entities', p.key()).filter('types', 'application').get()
                if not con:
                    con = Conversation()
                    con.types = ['application']
                    con.entities = [p.key()]
                con.participants = AddToList(p.key(), con.participants)
                con.put()

                mes = Message(parent=con)
                mes.person = p
                mes.text = message
                mes.put()

                emails = []
                for a in db.Query(Application).ancestor(p).filter('status', 'submitted').fetch(1000):
                    emails = AddToList(a.reception.communication_email, emails)

                if len(emails) < 1:
                    for reception in db.Query(Reception).fetch(1000):
                        emails = AddToList(reception.communication_email, emails)

                SendMail(
                    to = emails,
                    subject = Translate('application_message_email1_subject') % p.displayname,
                    message = Translate('application_message_email1_message') % {'name': p.displayname, 'link': SYSTEM_URL + '/reception/application/' + str(p.key()), 'text': mes.text }
                )

                emails = []
                if p.email:
                    emails = AddToList(p.email, emails)
                if p.apps_username:
                    emails = AddToList(p.apps_username, emails)
                for contact in db.Query(Contact).ancestor(p).filter('type', 'email').fetch(1000):
                    emails = AddToList(contact.value, emails)

                SendMail(
                    to = emails,
                    subject = Translate('application_message_email2_subject') % p.displayname,
                    message = Translate('application_message_email2_message') % mes.text
                )

                respond['date'] = UtcToLocalDateTime(mes.created).strftime('%d.%m.%Y %H:%M')
                respond['person'] = mes.person.displayname
                respond['message'] = mes.text

                self.response.out.write(simplejson.dumps(respond))


def main():
    Route([
            ('/application/signin', ShowSignin),
            ('/application/person', EditPerson),
            ('/application/contact', EditContact),
            ('/application/cv', EditCV),
            ('/application/message', PostMessage),
            ('/application/submit', SubmitApplication),
            ('/application/thanks', ShowSubmitApplication),
            (r'/application(.*)', ShowApplication),
        ])


if __name__ == '__main__':
    main()