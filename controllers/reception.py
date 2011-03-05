from django.utils import simplejson
import datetime

from bo import *
from database.application import *


class ShowReceptionList(boRequestHandler):
    def get(self):
        if self.authorize('reception'):
            receptions = db.Query(Reception).order('start_date').fetch(1000)

            for r in receptions:
                r.application_count_selected = db.Query(Application).filter('reception', r).filter('status', 'selected').count()
                r.application_count_submitted = db.Query(Application).filter('reception', r).filter('status', 'submitted').count()
                r.application_count_accepted = db.Query(Application).filter('reception', r).filter('status', 'accepted').count()

            self.view('reception', 'receptions/reception_list.html', {
                'receptions': receptions,
            })


class ShowApplicationList(boRequestHandler):
    def get(self, key):
        if self.authorize('reception'):
            key = key.strip('/')

            if not key:
                self.redirect('/reception')
                return

            r = Reception().get(key)

            #application_selected = db.Query(Application).filter('reception', r).filter('status', 'selected').count()
            #application_submitted = db.Query(Application).filter('reception', r).filter('status', 'submitted').count()
            #application_accepted = db.Query(Application).filter('reception', r).filter('status', 'accepted').count()

            applications = []
            for a in db.Query(Application).filter('reception', db.Key(key)).filter('status !=', 'unselected').fetch(1000):
                applications.append({
                    'status': Translate('application_status_' + a.status),
                    'person': a.parent().displayname,
                    'application': a,
                })

            self.view(Translate('reception') + ' - ' + r.name.translate(), 'receptions/application_list.html', {
                'reception': r,
                'applications': applications,
            })


class ShowApplication(boRequestHandler):
    def get(self, key):
        if self.authorize('reception'):
            key = key.strip('/')

            if not key:
                self.redirect('/reception')
                return

            p = Person().get(key)
            if p:
                now = datetime.now()
                receptions = []
                application_statuses = []
                for a in db.Query(Application).ancestor(p).filter('status !=', 'unselected').fetch(1000):
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
                    'post_url': '/reception',
                    'application_status': application_status,
                    'application_readonly': True,
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


class PostMessage(boRequestHandler):
    def post(self):
        if self.authorize('reception'):
            action = self.request.get('action').strip()
            person =  self.request.get('person').strip()
            message = self.request.get('message').strip()
            respond = {}

            if person:
                p = Person().get(person)
                if p and message:
                    con = db.Query(Conversation).filter('entities', p.key()).filter('types', 'application').get()
                    if not con:
                        con = Conversation()
                        con.types = ['application']
                        con.entities = [p.key()]
                    con.participants = AddToList(p.key(), con.participants)
                    con.participants = AddToList(Person().current.key(), con.participants)
                    con.put()

                    mes = Message(parent=con)
                    mes.person = Person().current
                    mes.text = message
                    mes.put()

                    emails = []
                    for a in db.Query(Application).ancestor(p).filter('status', 'selected').fetch(1000):
                        emails = AddToList(a.reception.communication_email, emails)

                    for a in db.Query(Application).ancestor(p).filter('status', 'submitted').fetch(1000):
                        a.status = 'selected'
                        a.put()
                        emails = AddToList(a.reception.communication_email, emails)

                    if len(emails) < 1:
                        for reception in db.Query(Reception).fetch(1000):
                            emails = AddToList(reception.communication_email, emails)

                    SendMail(
                        to = emails,
                        subject = Translate('application_message_email3_subject') % p.displayname,
                        message = Translate('application_message_email3_message') % {'name': Person().current.displayname, 'link': SYSTEM_URL + '/reception/application/' + str(p.key()), 'text': mes.text }
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
                        subject = Translate('application_message_email4_subject') % p.displayname,
                        message = Translate('application_message_email4_message') % {'name': Person().current.displayname, 'text': mes.text }
                    )

                    respond['date'] = UtcToLocalDateTime(mes.created).strftime('%d.%m.%Y %H:%M')
                    respond['person'] = mes.person.displayname
                    respond['message'] = mes.text

                    self.response.out.write(simplejson.dumps(respond))


class AcceptApplication(boRequestHandler):
    def post(self):
        if self.authorize('reception'):
            person =  self.request.get('person').strip()
            respond = {}

            if person:
                p = Person().get(person)
                if p:
                    emails = []
                    for a in db.Query(Application).ancestor(p).filter('status !=', 'unselected').fetch(1000):
                        a.status = 'accepted'
                        a.put()
                        emails = AddToList(a.reception.communication_email, emails)

                    con = db.Query(Conversation).filter('entities', p.key()).filter('types', 'application').get()
                    if not con:
                        con = Conversation()
                        con.types = ['application']
                        con.entities = [p.key()]
                    con.participants = AddToList(p.key(), con.participants)
                    con.participants = AddToList(Person().current.key(), con.participants)
                    con.put()

                    mes = Message(parent=con)
                    mes.person = Person().current
                    mes.text = Translate('application_accept_log_message')
                    mes.put()

                    SendMail(
                        to = emails,
                        subject = Translate('application_accept_email1_subject') % p.displayname,
                        message = Translate('application_accept_email1_message') % {'name': Person().current.displayname, 'link': SYSTEM_URL + '/reception/application/' + str(p.key()), 'text': mes.text }
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
                        subject = Translate('application_accept_email2_subject') % p.displayname,
                        message = Translate('application_accept_email2_message') % {'name': Person().current.displayname, 'text': mes.text }
                    )

                    respond['date'] = UtcToLocalDateTime(mes.created).strftime('%d.%m.%Y %H:%M')
                    respond['person'] = mes.person.displayname
                    respond['message'] = mes.text

                    self.response.out.write(simplejson.dumps(respond))


def main():
    Route([
            (r'/reception/application/(.*)', ShowApplication),
            ('/reception/message', PostMessage),
            ('/reception/accept', AcceptApplication),
            (r'/reception/(.*)', ShowApplicationList),
            ('/reception', ShowReceptionList),
        ])


if __name__ == '__main__':
    main()