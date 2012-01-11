from google.appengine.api import users
import datetime
import random
import string

from operator import attrgetter

from libraries.gmemsess import *

from bo import *
from database.bubble import *

class ShowSignin(boRequestHandler):
    def get(self):

        user = users.get_current_user()
        if user:
            self.redirect(users.create_logout_url('/application/signin'))

        sess = Session(self, timeout=86400)
        sess.invalidate()

        language = self.request.get('language', SystemPreferences().get('default_language')).strip()

        languages = []
        for l in SystemPreferences().get('languages'):
            if l != language:
                languages.append({'value': l, 'label': Translate('language_%s' % l, language=language)})

        self.view(
            language = language,
            main_template='main/print.html',
            template_file = 'application/signin.html',
            values = {
                'account_login_url': users.create_login_url('/application'),
                'languages': languages,
                'language': language,
            }
        )

    def post(self):
        email = self.request.get('email').strip()
        password = self.request.get('applicant_pass').strip()
        language = self.request.get('language').strip()

        if email:
            if CheckMailAddress(email):
                p = db.Query(Bubble).filter('type', 'applicant').filter('email', email).get()
                if not p:
                    p = db.Query(Bubble).filter('users', email).get()
                    if not p:
                        p = Bubble()
                        p.type = 'applicant'
                        p.email = email
                        p.put()

                password = ''.join(random.choice(string.ascii_letters) for x in range(2))
                password += str(p.key().id())
                password += ''.join(random.choice(string.ascii_letters) for x in range(3))
                password = password.replace('O', random.choice(string.ascii_lowercase))

                p.language = language
                p.password = password
                p.put()

                SendMail(
                    to = email,
                    reply_to = 'sisseastumine@artun.ee',
                    subject = Translate('application_signup_mail_subject', language),
                    message = Translate('application_signup_mail_message', language) % p.password
                )
                self.echo('OK', False)

        else:
            if password:
                b = db.Query(Bubble).filter('type', 'applicant').filter('password', password).get()
                if b:
                    sess = Session(self, timeout=86400)
                    sess['applicant_key'] = str(b.key())
                    sess.save()
                    self.response.out.write('OK')


class ShowApplication(boRequestHandler):
    def get(self):
        sess = Session(self, timeout=86400)
        if 'applicant_key' not in sess:
            self.redirect('/application/signin')
            return

        p = db.Query(Bubble).filter('type', 'applicant').filter('__key__', db.Key(sess['applicant_key'])).get()
        if not p:
            self.redirect('/application/signin')
            return

        language = self.request.get('language', p.language).strip()

        receptions = []
        leeching_count = 0
        for g in sorted(db.Query(Bubble).filter('type', 'reception_group').fetch(1000), key=attrgetter('sort_%s' % language)):
            gname = getattr(Dictionary.get(g.name), language)
            gname2 = ''
            for r in sorted(db.Query(Bubble).filter('type', 'reception').filter('__key__ IN', g.optional_bubbles).fetch(1000), key=attrgetter('sort_%s' % language)):
                for s in sorted(db.Query(Bubble).filter('type', 'submission').filter('__key__ IN', r.optional_bubbles).fetch(1000), key=attrgetter('sort_%s' % language)):
                    # if getattr(s, 'start_datetime', datetime.now()) < datetime.now() and getattr(s, 'end_datetime', datetime.now()) > datetime.now():
                    if getattr(s, 'start_date', datetime.now()) < datetime.now() and getattr(s, 'end_date', datetime.now()) > datetime.now():
                        br = db.Query(BubbleRelation).filter('bubble', s.key()).filter('related_bubble', p.key()).filter('type', 'leecher').filter('_is_deleted', False).get()
                        if br:
                            leeching_count += 1
                        receptions.append({
                            'key': str(s.key()),
                            'group': gname if gname != gname2 else None,
                            'displayname': getattr(Dictionary.get(s.name), language),
                            'url': s.url if hasattr(s, 'url') else None,
                            'is_selected': True if br else False,
                        })
                        gname2 = gname

        subbubbles = []
        for t in ['cv_edu', 'cv_work', 'applicant_doc']:
            props = []
            for b in db.Query(Bubble).filter('_is_deleted', False).filter('type', t).filter('__key__ IN', p.optional_bubbles).fetch(1000):
                props.append({'key': str(b.key()), 'props': b.GetProperties(language)})
            eb = Bubble()
            eb.type = t
            props.append({'key': None, 'props': eb.GetProperties(language)})
            ltype=db.Query(BubbleType).filter('type', t).get()
            subbubbles.append({'label': getattr(ltype.name_plural, language), 'info': getattr(ltype.description, language, ''), 'type': t, 'bubbles': props})

        languages = []
        for l in SystemPreferences().get('languages'):
            if l != language:
                languages.append({'value': l, 'label': Translate('language_%s' % l, language=language)})

        rgtype=db.Query(BubbleType).filter('type', 'reception').get()
        btype=db.Query(BubbleType).filter('type', 'applicant').get()

        self.view(
            language = language,
            main_template='main/print.html',
            template_file = 'application/application.html',
            values = {
                'languages': languages,
                'language': language,
                'bubble': p.GetProperties(language),
                'bubble_label': getattr(btype.name, language),
                'receptions': receptions,
                'receptions_label': getattr(rgtype.name_plural, language),
                'subbubbles': subbubbles,
                'leeching_count': leeching_count,
            }
        )

    def post(self):
        sess = Session(self, timeout=86400)
        if 'applicant_key' not in sess:
            return

        p = db.Query(Bubble).filter('type', 'applicant').filter('__key__', db.Key(sess['applicant_key'])).get()
        if not p:
            return

        value = p.SetProperty(
            propertykey = self.request.get('property').strip(),
            oldvalue = self.request.get('oldvalue').strip(),
            newvalue = self.request.get('newvalue').strip(),
        )
        self.echo(self.request.get('newvalue').strip(), False)


class EditSubmission(boRequestHandler):
    def post(self):
        sess = Session(self, timeout=86400)
        if 'applicant_key' not in sess:
            return

        p = db.Query(Bubble).filter('type', 'applicant').filter('__key__', db.Key(sess['applicant_key'])).get()
        if not p:
            return

        action = self.request.get('action').strip()
        bubblekey = self.request.get('bubble').strip()
        if not bubblekey:
            return

        br = db.Query(BubbleRelation).filter('bubble', db.Key(bubblekey)).filter('related_bubble', p.key()).filter('type', 'leecher').get()
        if action == 'add':
            if br:
                br._is_deleted = False
            else:
                br = BubbleRelation()
                br.type = 'leecher'
                br.bubble = db.Key(bubblekey)
                br.related_bubble = p.key()
            br.put()
        else:
            if br:
                br._is_deleted = True
                br.put()


class EditCV(boRequestHandler):
    def post(self):
        sess = Session(self, timeout=86400)
        if 'applicant_key' not in sess:
            return

        p = db.Query(Bubble).filter('type', 'applicant').filter('__key__', db.Key(sess['applicant_key'])).get()
        if not p:
            return

        bubblekey = self.request.get('bubble').strip()
        if bubblekey:
            bubble = Bubble().get(bubblekey)
        else:
            bubble = Bubble()
            bubble.type = self.request.get('type').strip()
            bubble.put()
            p.optional_bubbles = AddToList(bubble.key(), p.optional_bubbles)
            p.put()

        value = bubble.SetProperty(
            propertykey = self.request.get('property').strip(),
            oldvalue = self.request.get('oldvalue').strip(),
            newvalue = self.request.get('newvalue').strip(),
        )

        self.echo(str(bubble.key()), False)





# def CheckApplication(person):
#     missing = []
#     if not person.forename:
#         missing.append('forename')
#     if not person.surname:
#         missing.append('surname')
#     if not person.idcode:
#         missing.append('idcode')
#     if not person.gender:
#         missing.append('gender')
#     if not person.birth_date:
#         missing.append('birthdate')
#     if not person.photo:
#         missing.append('photo')

#     if db.Query(Cv).ancestor(person).filter('type', 'secondary_education').count() < 1:
#         missing.append('application_edu_secondary')


#     if len(missing) > 0:
#         return '<span style="color:red">' + (Translate('application_info_missing') % rReplace(', '.join([Translate(m).lower() for m in missing]), ',', ' ' + Translate('and'), 1)) + '</span>'
#     else:
#         return Translate('application_info_complete')




# # Should probably be part of BO and named differently, too
# class ListRatings(boRequestHandler):
#     head = []
#     data = []


# class ShowPersonRatings(boRequestHandler):
#     def get(self):

#         person = Person().current_s(self)
#         if not person:
#             self.redirect('/application/signin')
#             return

#         changeinfo = ''
#         last_change = person.last_change
#         if last_change:
#             if last_change.user:
#                 changer = db.Query(Person).filter('user', last_change.user).get()
#                 if changer:
#                     changeinfo = Translate('person_changed_on') % {'name': changer.displayname, 'date': UtcToLocalDateTime(last_change.datetime).strftime('%d.%m.%Y %H:%M')}

#         grades = db.Query(Grade).filter('person',person.key()).fetch(1000)
#         grades = sorted(grades, key=lambda k: k.datetime, reverse=True)

#         ratings = ListRatings()
#         ratings.head = [
#             Translate('bubble_displayname').encode("utf-8"),
#             Translate('grade_name').encode("utf-8"),
#             Translate('grade_equivalent').encode("utf-8"),
#             Translate('date').encode("utf-8"),
#         ]
#         ratings.data = []
#         for grade in grades:
#             rating = []
#             if not grade.bubble_type in ['reception','exam_group','exam','state_exam',]:
#                 continue
#             rating.append( grade.bubble.displayname + ' (' + str(grade.bubble.key().id()) + '), ' + grade.bubble_type )
#             rating.append( grade.displayname )
#             rating.append( grade.equivalent )
#             rating.append( grade.displaydate )
#             ratings.data.append(rating)

#         if len(ratings.data) == 0:
#             self.redirect('/application')
#             return

#         self.view(person.displayname, 'application/ratings.html', {
#             'person': person,
#             'table_data': ratings,
#             'changed': changeinfo,
#         })


# class ShowApplication(boRequestHandler):
#     def get(self, url):
#         p =  Person().current_s(self)
#         if not p:
#             self.redirect('/application/signin')
#         else:
#             now = datetime.now()

#             receptions = []
#             for r in db.Query(Bubble).filter('type', 'submission').filter('start_datetime <=', datetime.now()).filter('is_deleted', False).fetch(1000):
#                 if r.end_datetime:
#                     if r.end_datetime >= datetime.now():
#                         r.end = Translate('reception_will_end_on') % r.end_datetime.strftime('%d.%m.%Y')
#                         if r.key() in p.leecher:
#                             r.selected = True
#                         level_r = db.Query(Bubble).filter('type', 'reception').filter('optional_bubbles', r.key()).get()
#                         level_rs = db.Query(Bubble).filter('type', 'receptions').filter('optional_bubbles', level_r.key()).get()
#                         if level_rs:
#                             r.level = level_rs.displayname
#                         else:
#                             r.level = ''
#                         receptions.append(r)

#             documents = db.Query(Document).filter('entities', p.key()).filter('types', 'application_document').fetch(1000)
#             secondaryschools = db.Query(Cv).ancestor(p).filter('type', 'secondary_education').fetch(1000)
#             highschools = db.Query(Cv).ancestor(p).filter('type', 'higher_education').fetch(1000)
#             workplaces = db.Query(Cv).ancestor(p).filter('type', 'workplace').fetch(1000)
#             stateexams = db.Query(Bubble).filter('type', 'state_exam').filter('start_datetime <=', datetime.now()).filter('is_deleted', False).fetch(1000)
#             for se in stateexams:
#                 se_grade = db.Query(Grade).filter('person', p).filter('bubble', se).filter('is_deleted', False).get()
#                 if se_grade:
#                     se.grade = se_grade.gradedefinition.key()

#             conversation = db.Query(Conversation).filter('entities', p.key()).filter('types', 'application').get()
#             if conversation:
#                 messages = db.Query(Message).ancestor(conversation).fetch(1000)
#                 for message in messages:
#                     message.created = UtcToLocalDateTime(message.created)
#             else:
#                 messages = {}

#             self.view('application', 'application/application.html', {
#                 'post_url': '/application',
#                 'receptions': receptions,
#                 'stateexams': stateexams,
#                 'person': p,
#                 'date_days': range(1, 32),
#                 'date_months': Translate('list_months').split(','),
#                 'document_types': Translate('application_documents_types').split(','),
#                 'date_years': range((now.year-15), (now.year-90), -1),
#                 'photo_upload_url': blobstore.create_upload_url('/document/upload'),
#                 'document_upload_url': blobstore.create_upload_url('/document/upload'),
#                 'documents': documents,
#                 'secondaryschools': secondaryschools,
#                 'highschools': highschools,
#                 'workplaces': workplaces,
#                 'messages': messages,
#                 'application_completed_info': CheckApplication(p),
#             })

#     def post(self, url):
#         p =  Person().current_s(self)
#         if p:
#             key = self.request.get('key').strip()
#             field = self.request.get('field').strip()
#             value = self.request.get('value').strip()
#             respond = {}

#             if value.lower() == 'true':
#                 p.add_leecher(db.Key(key))
#             else:
#                 p.remove_leecher(db.Key(key))

#             respond['key'] = key
#             self.echo_json(respond)


# class EditPerson(boRequestHandler):
#     def post(self):
#         p =  Person().current_s(self)
#         if p:
#             field = self.request.get('field').strip()
#             value = self.request.get('value').strip()
#             respond = {}

#             if field in ['forename', 'surname', 'idcode', 'gender', 'citizenship', 'country_of_residence']:
#                 setattr(p, field, value)

#             if field == 'birthdate':
#                 if value:
#                     p.birth_date = datetime.strptime(value, '%d.%m.%Y').date()
#                 else:
#                     p.birth_date = None

#             if field == 'have_been_subsidised':
#                 if value.lower() == 'true':
#                     p.have_been_subsidised = True
#                 else:
#                     p.have_been_subsidised = False

#             p.put()

#             respond['application_completed_info'] = CheckApplication(p)

#             self.echo_json(respond)


# class EditContact(boRequestHandler):
#     def post(self):
#         p =  Person().current_s(self)
#         if p:
#             key = self.request.get('key').strip()
#             type = self.request.get('type').strip()
#             value = self.request.get('value').strip()
#             respond = {}

#             if key:
#                 c = Contact().get(key)
#                 if value:
#                     c.type = type
#                     c.value = value
#                     c.put()
#                     response_key = str(c.key())
#                 else:
#                     c.delete()
#                     response_key = ''
#             else:
#                 c = Contact(parent=p)
#                 c.type = type
#                 c.value = value
#                 c.put()
#                 response_key = str(c.key())

#             respond['key'] = response_key

#             p.put()
#             self.echo_json(respond)


# class EditCV(boRequestHandler):
#     def post(self):
#         p =  Person().current_s(self)
#         if p:
#             key = self.request.get('key').strip()
#             field = self.request.get('field').strip()
#             value = self.request.get('value').strip()
#             type = self.request.get('type').strip()
#             respond = {}

#             if key:
#                 cv = Cv().get(key)
#             else:
#                 cv = Cv(parent=p)
#                 cv.type = type

#             if field in ['organisation','start', 'end', 'description']:
#                 setattr(cv, field, value)

#             cv.put()
#             respond['key'] = str(cv.key())
#             respond['application_completed_info'] = CheckApplication(p)

#             self.echo_json(respond)


# class StateExam(boRequestHandler):
#     def post(self):
#         p =  Person().current_s(self)
#         if p:
#             gradedefinition_key = self.request.get('value').strip()
#             bubble_key = self.request.get('exam').strip()
#             respond = {}

#             bubble = Bubble().get(bubble_key)

#             if gradedefinition_key:
#                 gradedefinition = GradeDefinition().get(gradedefinition_key)
#             else:
#                 gradedefinition = None

#             grade = db.Query(Grade).filter('person', p).filter('bubble', bubble).get()
#             if not grade:
#                 grade = Grade()
#                 grade.person = p
#                 grade.bubble = bubble
#             grade.bubble_type = bubble.type
#             grade.datetime = datetime.now()
#             #grade.name =
#             grade.points = bubble.points
#             #grade.school =
#             #grade.teacher =
#             #grade.teacher_name =
#             if gradedefinition:
#                 grade.gradedefinition = gradedefinition
#                 grade.equivalent = gradedefinition.equivalent
#                 grade.is_positive = gradedefinition.is_positive
#                 grade.is_deleted = False
#             else:
#                 grade.is_deleted = True
#             grade.put()


#             respond['application_completed_info'] = CheckApplication(p)

#             self.echo_json(respond)


# class PostMessage(boRequestHandler):
#     def post(self):
#         p =  Person().current_s(self)
#         if p:
#             message = self.request.get('message').strip()
#             respond = {}

#             if message:
#                 con = db.Query(Conversation).filter('entities', p.key()).filter('types', 'application').get()
#                 if not con:
#                     con = Conversation()
#                     con.types = ['application']
#                     con.entities = [p.key()]
#                 con.participants = AddToList(p.key(), con.participants)
#                 con.put()

#                 mes = Message(parent=con)
#                 mes.person = p
#                 mes.text = message
#                 mes.put()

#                 SendMail(
#                     to = 'sisseastumine@artun.ee',
#                     reply_to = 'sisseastumine@artun.ee',
#                     subject = Translate('application_message_email1_subject') % p.displayname,
#                     message = Translate('application_message_email1_message') % {'name': p.displayname, 'link': 'http://bubbledu.artun.ee/reception/application/' + str(p.key()), 'text': mes.text }
#                 )

#                 SendMail(
#                     to = p.emails,
#                     reply_to = 'sisseastumine@artun.ee',
#                     subject = Translate('application_message_email2_subject') % p.displayname,
#                     message = Translate('application_message_email2_message') % mes.text
#                 )

#                 respond['date'] = UtcToLocalDateTime(mes.created).strftime('%d.%m.%Y %H:%M')
#                 respond['person'] = mes.person.displayname
#                 respond['message'] = mes.text

#                 self.echo_json(respond)


def main():
    Route([
            ('/application/signin', ShowSignin),
            ('/application/leech', EditSubmission),
            ('/application/cv', EditCV),
            ('/application', ShowApplication),
            # ('/application/ratings', ShowPersonRatings),
            # ('/application/person', EditPerson),
            # ('/application/contact', EditContact),
            # ('/application/cv', EditCV),
            # ('/application/stateexam', StateExam),
            # ('/application/message', PostMessage),
        ])


if __name__ == '__main__':
    main()
