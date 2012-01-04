from google.appengine.api import users
import datetime

from bo import *
from database.bubble import *
from database.person import *


class ShowReceptionList(boRequestHandler):
    def get(self):
        if self.authorize('reception'):
            receptions = db.Query(Bubble).filter('type', 'submission').filter('is_deleted', False).order('start_datetime').fetch(1000000)
            for r in receptions:
                level_r = db.Query(Bubble).filter('type', 'reception').filter('optional_bubbles', r.key()).get()
                level_rs = db.Query(Bubble).filter('type', 'receptions').filter('optional_bubbles', level_r.key()).get()
                if level_rs:
                    r.level = level_rs.displayname
                else:
                    r.level = ''

            self.view('reception', 'receptions/reception_list.html', {
                'receptions': receptions,
            })

class ShowApplicationList(boRequestHandler):
    def get(self, bubble_id):
        if self.authorize('reception'):
            bubble_id = bubble_id.strip('/')

            if not bubble_id:
                self.redirect('/reception')
                return

            person = Person().current
            reception = Bubble().get_by_id(int(bubble_id))
            leechers = reception.leechers2

            for leecher in leechers:
                leecher.is_new = True
                accesslog = db.Query(AccessLog).filter('user', users.User(person.user)).filter('path', '/reception/application/' + str(leecher.key())).order('-datetime').get()
                if accesslog:
                    leecher.access = accesslog.datetime
                    if leecher.changed < accesslog.datetime:
                        leecher.is_new = False

                grade = db.Query(Grade).filter('bubble', reception).filter('person', leecher).filter('is_deleted', False).get()
                if grade:
                    gd = grade.gradedefinition
                    leecher.grade_key = gd.key()
                    leecher.grade_equivalent = gd.equivalent
                    leecher.grade_displayname = gd.displayname
                else:
                    leecher.grade_key = None
                    leecher.grade_equivalent = 999999
                    leecher.grade_displayname = Translate('bubble_not_rated')


            self.view(Translate('reception') + ' - ' + reception.displayname, 'receptions/application_list.html', {
                'reception': reception,
                'leechers': leechers,
            })


class ShowApplication(boRequestHandler):
    def get(self, key):
        if self.authorize('reception'):
            key = key.strip('/')
            now = datetime.now()

            if not key:
                self.redirect('/reception')
                return

            p = Person().get(key)
            if p:

                submissions = []
                for s in db.Query(Bubble).filter('type', 'submission').filter('start_datetime <', datetime.now()).filter('is_deleted', False).fetch(1000):
                    if s.end_datetime:
                        if s.end_datetime > datetime.now():
                            level_r = db.Query(Bubble).filter('type', 'reception').filter('optional_bubbles', s.key()).get()
                            level_rs = db.Query(Bubble).filter('type', 'receptions').filter('optional_bubbles', level_r.key()).get()
                            if level_rs:
                                s.level = level_rs.displayname
                            else:
                                s.level = ''
                            submissions.append(s)

                receptions = db.Query(Bubble).filter('leechers', p).filter('type', 'submission').fetch(1000)
                for r in receptions:
                    r.name_str = r.name.value
                    r.end = Translate('reception_will_end_on') % r.end_datetime.strftime('%d.%m.%Y')
                    if r.key() in p.leecher:
                        r.selected = True
                    level_r = db.Query(Bubble).filter('type', 'reception').filter('optional_bubbles', r.key()).get()
                    level_rs = db.Query(Bubble).filter('type', 'receptions').filter('optional_bubbles', level_r.key()).get()
                    if level_rs:
                        r.level = level_rs.displayname
                    else:
                        r.level = ''

                    r.gradedefinitions = r.rating_scale.gradedefinitions

                    grade = db.Query(Grade).filter('bubble', r).filter('person', p).filter('is_deleted', False).get()
                    if grade:
                        r.grade_key = grade.gradedefinition.key()
                        r.grade_is_locked = grade.is_locked
                    else:
                        r.grade_key = None

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
                    'post_url': '/reception',
                    'receptions': receptions,
                    'stateexams': stateexams,
                    'submissions': submissions,
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

                    SendMail(
                        to = p.emails,
                        reply_to = 'sisseastumine@artun.ee',
                        subject = Translate('application_message_email4_subject') % p.displayname,
                        message = Translate('application_message_email4_message') % {'name': Person().current.displayname, 'text': mes.text }
                    )

                    respond['date'] = UtcToLocalDateTime(mes.created).strftime('%d.%m.%Y %H:%M')
                    respond['person'] = mes.person.displayname
                    respond['message'] = mes.text

                    self.echo_json(respond)


class EditPerson(boRequestHandler):
    def post(self):
        if self.authorize('reception'):
            person =  self.request.get('person').strip()
            field = self.request.get('field').strip()
            value = self.request.get('value').strip()
            respond = {}

            if person:
                p = Person().get(person)
                if p:

                    if field in ['forename', 'surname', 'idcode', 'gender', 'citizenship', 'country_of_residence']:
                        p.index_names()
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

            self.echo_json(respond)


class EditContact(boRequestHandler):
    def post(self):
        if self.authorize('reception'):
            person =  self.request.get('person').strip()
            key = self.request.get('key').strip()
            type = self.request.get('type').strip()
            value = self.request.get('value').strip()
            respond = {}

            if person:
                p = Person().get(person)
                if p:
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
                    self.echo_json(respond)


class EditCV(boRequestHandler):
    def post(self):
        if self.authorize('reception'):
            person =  self.request.get('person').strip()
            key = self.request.get('key').strip()
            field = self.request.get('field').strip()
            type = self.request.get('type').strip()
            value = self.request.get('value').strip()
            respond = {}

            if person:
                p = Person().get(person)
                if p:
                    if key:
                        cv = Cv().get(key)
                    else:
                        cv = Cv(parent=p)
                        cv.type = type

                    if field in ['organisation','start', 'end', 'description']:
                        setattr(cv, field, value)

                    cv.put()
                    respond['key'] = str(cv.key())

                    self.echo_json(respond)


class StateExam(boRequestHandler):
    def post(self):
        if self.authorize('bubbler'):
            bubble_key = self.request.get('exam').strip()
            person_key = self.request.get('person').strip()
            gradedefinition_key = self.request.get('value').strip()

            bubble = Bubble().get(bubble_key)

            if gradedefinition_key:
                gradedefinition = GradeDefinition().get(gradedefinition_key)
            else:
                gradedefinition = None

            grade = db.Query(Grade).filter('person', db.Key(person_key)).filter('bubble', bubble).get()
            if not grade:
                grade = Grade()
                grade.person = db.Key(person_key)
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


class AddSubmission(boRequestHandler):
    def post(self):
        if self.authorize('bubbler'):
            bubble_key = self.request.get('bubble').strip()
            person_key = self.request.get('person').strip()

            person = Person().get(person_key)
            person.add_leecher(db.Key(bubble_key))
            person.put()


class RateApplication(boRequestHandler):
    def post(self):
        if self.authorize('bubbler'):
            bubble_key = self.request.get('bubble').strip()
            person_key = self.request.get('person').strip()
            gradedefinition_key = self.request.get('grade').strip()

            bubble = Bubble().get(bubble_key)

            if gradedefinition_key:
                gradedefinition = GradeDefinition().get(gradedefinition_key)
            else:
                gradedefinition = None

            grade = db.Query(Grade).filter('person', db.Key(person_key)).filter('bubble', bubble).get()
            if not grade:
                grade = Grade()
                grade.person = db.Key(person_key)
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


class LockRating(boRequestHandler):
    def get(self, person_key):
        if self.authorize('bubbler'):
            person_key = person_key.strip('/')
            if person_key:
                person = Person.get(person_key)

                for bubble in db.Query(Bubble).filter('leechers', person).filter('type', 'submission').fetch(1000):
                    for g in db.Query(Grade).filter('is_deleted', False).filter('is_locked', False).filter('person', person).filter('bubble', bubble).fetch(1000):
                        g.is_locked = True
                        g.put()

                        if g.is_positive == True:
                            taskqueue.Task(url='/taskqueue/bubble_pass_leechers', params={'bubble_key': str(g.bubble.key()), 'person_key': str(g.person.key())}).add(queue_name='one-by-one')

                self.redirect('/reception/application/' + person_key)


class Stats(boRequestHandler):
    def get(self):
        email = Person().current.primary_email
        taskqueue.Task(url='/taskqueue/application_stats', params={'email': email}).add()
        self.echo('Email sent to ' + email)


def main():
    Route([
            (r'/reception/application/(.*)', ShowApplication),
            ('/reception/add_submission', AddSubmission),
            ('/reception/rate', RateApplication),
            ('/reception/person', EditPerson),
            ('/reception/contact', EditContact),
            ('/reception/cv', EditCV),
            ('/reception/stateexam', StateExam),
            ('/reception/message', PostMessage),
            ('/reception/stats', Stats),
            (r'/reception/lock/(.*)', LockRating),
            (r'/reception/(.*)', ShowApplicationList),
            ('/reception', ShowReceptionList),
        ])


if __name__ == '__main__':
    main()
