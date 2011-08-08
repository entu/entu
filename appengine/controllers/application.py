from google.appengine.api import users
from django.utils import simplejson
import datetime
import random
import string

from bo import *
from database.bubble import *
from database.person import *
from libraries.gmemsess import *

def CheckApplication(person):
    missing = []
    if not person.forename:
        missing.append('forename')
    if not person.surname:
        missing.append('surname')
    if not person.idcode:
        missing.append('idcode')
    if not person.gender:
        missing.append('gender')
    if not person.birth_date:
        missing.append('birthdate')
    if not person.photo:
        missing.append('photo')

    if db.Query(Cv).ancestor(person).filter('type', 'secondary_education').count() < 1:
        missing.append('application_edu_secondary')


    if len(missing) > 0:
        return '<span style="color:red">' + (Translate('application_info_missing') % rReplace(', '.join([Translate(m).lower() for m in missing]), ',', ' ' + Translate('and'), 1)) + '</span>'
    else:
        return Translate('application_info_complete')


class ShowSignin(boRequestHandler):
    def get(self):

        user = users.get_current_user()
        if user:
            self.redirect(users.create_logout_url('/application/signin'))

        sess = Session(self, timeout=86400)
        sess.invalidate()

        self.view('application', 'application/signup.html', {
            'account_login_url': users.create_login_url('/application/ratings'),
        })

    def post(self):

        email = self.request.get('email').strip()
        password = self.request.get('applicant_pass').strip()

        if email:
            if CheckMailAddress(email):
                p = db.Query(Person).filter('email', email).get()
                if not p:
                    p = db.Query(Person).filter('apps_username', email).get()
                    if not p:
                        p = Person()
                        p.email = email
                        p.idcode = ''
                        if self.request.get('receptionist').strip() == 'receptionist':
                            p.model_version = 'QQQ'
                        else:
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

                SendMail(
                    to = email,
                    reply_to = 'sisseastumine@artun.ee',
                    subject = Translate('application_signup_mail_subject'),
                    message = Translate('application_signup_mail_message') % p.password
                )
                if self.request.get('receptionist').strip() == 'receptionist':
                    self.echo(str(p.key()), False)
                else:
                    self.echo('OK', False)

        else:
            if password:
                p = db.Query(Person).filter('password', password).get()
                if p:
                    sess = Session(self, timeout=86400)
                    sess['application_person_key'] = p.key()
                    sess.save()
                    self.response.out.write('OK')


# Should probably be part of BO and named differently, too
class ListRatings(boRequestHandler):
    head = []
    data = []


class ShowPersonRatings(boRequestHandler):
    def get(self):

        person = Person().current_s(self)
        if not person:
            self.redirect('/application/signin')
            return

        changeinfo = ''
        last_change = person.last_change
        if last_change:
            if last_change.user:
                changer = db.Query(Person).filter('apps_username', last_change.user).get()
                if changer:
                    changeinfo = Translate('person_changed_on') % {'name': changer.displayname, 'date': UtcToLocalDateTime(last_change.datetime).strftime('%d.%m.%Y %H:%M')}

        grades = db.Query(Grade).filter('person',person.key()).fetch(1000)
        grades = sorted(grades, key=lambda k: k.datetime, reverse=True)
        
        ratings = ListRatings()
        ratings.head = [
            Translate('bubble_displayname').encode("utf-8"),
            Translate('grade_name').encode("utf-8"),
            Translate('grade_equivalent').encode("utf-8"),
            Translate('date').encode("utf-8"),
        ]
        ratings.data = []
        for grade in grades:
            rating = []
            if not grade.bubble_type in ['reception','exam_group','exam','state_exam',]:
                continue
            rating.append( grade.bubble.displayname + ' (' + str(grade.bubble.key().id()) + '), ' + grade.bubble_type )
            rating.append( grade.displayname )
            rating.append( grade.equivalent )
            rating.append( grade.displaydate )
            ratings.data.append(rating)

        if len(ratings.data) == 0:
            self.redirect('/application')
            return

        self.view(person.displayname, 'application/ratings.html', {
            'person': person,
            'table_data': ratings,
            'changed': changeinfo,
        })


class ShowApplication(boRequestHandler):
    def get(self, url):
        p =  Person().current_s(self)
        if not p:
            self.redirect('/application/signin')
        else:
            now = datetime.now()

            receptions = []
            for r in db.Query(Bubble).filter('type', 'submission').filter('start_datetime <=', datetime.now()).filter('is_deleted', False).fetch(1000):
                if r.end_datetime:
                    if r.end_datetime >= datetime.now():
                        r.end = Translate('reception_will_end_on') % r.end_datetime.strftime('%d.%m.%Y')
                        if r.key() in p.leecher:
                            r.selected = True
                        level_r = db.Query(Bubble).filter('type', 'reception').filter('optional_bubbles', r.key()).get()
                        level_rs = db.Query(Bubble).filter('type', 'receptions').filter('optional_bubbles', level_r.key()).get()
                        if level_rs:
                            r.level = level_rs.displayname
                        else:
                            r.level = ''
                        receptions.append(r)

            documents = db.Query(Document).filter('entities', p.key()).filter('types', 'application_document').fetch(1000)
            secondaryschools = db.Query(Cv).ancestor(p).filter('type', 'secondary_education').fetch(1000)
            highschools = db.Query(Cv).ancestor(p).filter('type', 'higher_education').fetch(1000)
            workplaces = db.Query(Cv).ancestor(p).filter('type', 'workplace').fetch(1000)
            stateexams = db.Query(Bubble).filter('type', 'state_exam').filter('start_datetime <=', datetime.now()).filter('is_deleted', False).fetch(1000)
            for se in stateexams:
                se_grade = db.Query(Grade).filter('person', p).filter('bubble', se).filter('is_deleted', False).get()
                if se_grade:
                    se.grade = se_grade.gradedefinition.key()

            conversation = db.Query(Conversation).filter('entities', p.key()).filter('types', 'application').get()
            if conversation:
                messages = db.Query(Message).ancestor(conversation).fetch(1000)
                for message in messages:
                    message.created = UtcToLocalDateTime(message.created)
            else:
                messages = {}

            self.view('application', 'application/application.html', {
                'post_url': '/application',
                'receptions': receptions,
                'stateexams': stateexams,
                'person': p,
                'date_days': range(1, 32),
                'date_months': Translate('list_months').split(','),
                'document_types': Translate('application_documents_types').split(','),
                'date_years': range((now.year-15), (now.year-90), -1),
                'photo_upload_url': blobstore.create_upload_url('/document/upload'),
                'document_upload_url': blobstore.create_upload_url('/document/upload'),
                'documents': documents,
                'secondaryschools': secondaryschools,
                'highschools': highschools,
                'workplaces': workplaces,
                'messages': messages,
                'application_completed_info': CheckApplication(p),
            })

    def post(self, url):
        p =  Person().current_s(self)
        if p:
            key = self.request.get('key').strip()
            field = self.request.get('field').strip()
            value = self.request.get('value').strip()
            respond = {}

            if value.lower() == 'true':
                p.add_leecher(db.Key(key))
            else:
                p.remove_leecher(db.Key(key))

            respond['key'] = key
            self.response.out.write(simplejson.dumps(respond))


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

            respond['application_completed_info'] = CheckApplication(p)

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
            respond['application_completed_info'] = CheckApplication(p)

            self.response.out.write(simplejson.dumps(respond))


class StateExam(boRequestHandler):
    def post(self):
        p =  Person().current_s(self)
        if p:
            gradedefinition_key = self.request.get('value').strip()
            bubble_key = self.request.get('exam').strip()
            respond = {}

            bubble = Bubble().get(bubble_key)

            if gradedefinition_key:
                gradedefinition = GradeDefinition().get(gradedefinition_key)
            else:
                gradedefinition = None

            grade = db.Query(Grade).filter('person', p).filter('bubble', bubble).get()
            if not grade:
                grade = Grade()
                grade.person = p
                grade.bubble = bubble
            grade.bubble_type = bubble.type
            grade.datetime = datetime.now()
            #grade.name =
            grade.points = bubble.points
            #grade.school =
            #grade.teacher =
            #grade.teacher_name =
            if gradedefinition:
                grade.gradedefinition = gradedefinition
                grade.equivalent = gradedefinition.equivalent
                grade.is_positive = gradedefinition.is_positive
                grade.is_deleted = False
            else:
                grade.is_deleted = True
            grade.put()


            respond['application_completed_info'] = CheckApplication(p)

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

                SendMail(
                    to = 'sisseastumine@artun.ee',
                    reply_to = 'sisseastumine@artun.ee',
                    subject = Translate('application_message_email1_subject') % p.displayname,
                    message = Translate('application_message_email1_message') % {'name': p.displayname, 'link': SYSTEM_URL + '/reception/application/' + str(p.key()), 'text': mes.text }
                )

                SendMail(
                    to = p.emails,
                    reply_to = 'sisseastumine@artun.ee',
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
            ('/application/ratings', ShowPersonRatings),
            ('/application/person', EditPerson),
            ('/application/contact', EditContact),
            ('/application/cv', EditCV),
            ('/application/stateexam', StateExam),
            ('/application/message', PostMessage),
            (r'/application(.*)', ShowApplication),
        ])


if __name__ == '__main__':
    main()