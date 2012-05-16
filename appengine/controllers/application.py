from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import users
from google.appengine.api import images
from operator import attrgetter

import datetime
import random
import string
import urllib

from libraries.gmemsess import *

from bo import *
from database.bubble import *
from django.utils import simplejson


class ShowSignin(boRequestHandler):
    def get(self):

        user = users.get_current_user()
        if user:
            self.redirect(users.create_logout_url('/application/signin'))

        sess = Session(self)
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
                'account_login_url': users.create_logout_url(users.create_login_url('/application')),
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
                p = db.Query(Bubble).filter('type', 'pre_applicant').filter('email', email).get()
                if not p:
                    p = db.Query(Bubble).filter('type', 'applicant').filter('email', email).get()
                if not p:
                    p = db.Query(Bubble).filter('user', email).get()
                    if not p:
                        bt = db.Query(Bubble).filter('type', 'bubble_type').filter('path', 'pre_applicant').get()
                        p = Bubble()
                        p.type = bt.path
                        p.x_type = bt.key()
                        p.email = email
                        p.put(email)

                password = ''.join(random.choice(string.ascii_letters) for x in range(2))
                password += str(p.key().id())
                password += ''.join(random.choice(string.ascii_letters) for x in range(3))
                password = password.replace('O', random.choice(string.ascii_lowercase))

                p.language = language
                p.password = password
                p.put(getattr(p, 'email', ''))
                p.AutoFix()

                for k in ['agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUY4PvbAgw', 'agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYwLLLAgw', 'agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYyvrLAgw', 'agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUY1IfMAgw', 'agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYy_rLAgw']:
                    AddTask('/taskqueue/rights', {
                        'bubble': str(p.key()),
                        'person': str(db.Key(k)),
                        'right': 'viewer',
                        'user': getattr(p, 'email', '')
                    }, 'one-by-one')

                SendMail(
                    to = email,
                    reply_to = 'sisseastumine@artun.ee',
                    subject = Translate('application_signup_mail_subject', language),
                    message = Translate('application_signup_mail_message', language) % p.password
                )
                self.echo('OK', False)

        else:
            if password:
                b = db.Query(Bubble).filter('type', 'pre_applicant').filter('password', password).get()
                if not b:
                    b = db.Query(Bubble).filter('type', 'applicant').filter('password', password).get()
                if b:
                    sess = Session(self)
                    sess['applicant_key'] = str(b.key())
                    sess.save()
                    self.response.out.write('OK')


class ShowApplication(boRequestHandler):
    def get(self):
        language = self.request.get('language', SystemPreferences().get('default_language')).strip()

        user = users.get_current_user()
        if user:
            p = db.Query(Bubble).filter('user', user.email()).filter('x_is_deleted', False).get()
            if not p:
                self.redirect('/application/signin')
                return
            if p.type != 'applicant':
                bt = db.Query(Bubble).filter('type', 'bubble_type').filter('path', 'pre_applicant').get()
                p.type = bt.path
                p.x_type = bt.key()
                p.put()
            if not hasattr(p, 'email'):
                p.email = p.GetValue('user', '')
                p.put()
        else:
            sess = Session(self)
            if 'applicant_key' not in sess:
                self.redirect('/application/signin')
                return
            p = db.Query(Bubble).filter('type', 'pre_applicant').filter('__key__', db.Key(sess['applicant_key'])).get()
            if not p:
                p = db.Query(Bubble).filter('type', 'applicant').filter('__key__', db.Key(sess['applicant_key'])).get()
            if not p:
                self.redirect('/application/signin')
                return

        if getattr(p, 'language', '') != language:
            p.language = language
            p.put()

        if p.key() not in p.GetValueAsList('x_br_viewer'):
            setattr(p, 'x_br_viewer', ListMerge(p.key(), p.GetValueAsList('x_br_viewer')))
            p.put()

        receptions = []
        leeching_count = 0
        for g in sorted(db.Query(Bubble).filter('type', 'reception_group').fetch(1000), key=attrgetter('x_sort_%s' % language)):
            gname = getattr(Dictionary.get(g.name), language)
            gname2 = ''
            for r in sorted(g.GetRelatives('subbubble', 'reception'), key=attrgetter('x_sort_%s' % language)):
                for s in sorted(r.GetRelatives('subbubble', 'submission'), key=attrgetter('x_sort_%s' % language)):
                    if not getattr(Dictionary.get(s.name), language, False):
                        continue
                    leeching = p.key() in s.GetValueAsList('x_br_leecher')
                    if (getattr(s, 'start_datetime', datetime.now()) < datetime.now() and getattr(s, 'end_datetime', datetime.now()) > datetime.now()) or leeching:
                        if leeching:
                            leeching_count += 1
                        receptions.append({
                            'key': str(s.key()),
                            'group': gname if gname != gname2 else None,
                            'displayname': getattr(Dictionary.get(s.name), language),
                            'url': s.url if hasattr(s, 'url') else None,
                            'is_selected': leeching,
                            'is_open': getattr(s, 'start_datetime', datetime.now()) < datetime.now() and getattr(s, 'end_datetime', datetime.now()) > datetime.now()
                        })
                        gname2 = gname

        subbubbles = []
        for t in ['cv_edu', 'cv_edu_ba', 'cv_edu_ma', 'cv_work', 'state_exam', 'applicant_doc', 'message']:
            props = []
            for b in sorted(Bubble.get(p.GetValueAsList('x_br_subbubble')), key=attrgetter('x_created')):
                if b:
                    if b.type == t and b.x_is_deleted == False:
                        props.append({'key': str(b.key()), 'props': b.GetProperties(language)})
            eb = Bubble()
            eb.type = t
            eb.x_created = None
            props.append({'key': None, 'props': eb.GetProperties(language)})
            ltype = db.Query(Bubble).filter('type', 'bubble_type').filter('path', t).get()
            subbubbles.append({
                'label': GetDictionaryValue(ltype.name_plural, language) if hasattr(ltype, 'name_plural') else '',
                'info': GetDictionaryValue(ltype.description, language) if hasattr(ltype, 'description') else '',
                'type': t,
                'bubbles': props
            })

        languages = []
        for l in SystemPreferences().get('languages'):
            if l != language:
                languages.append({'value': l, 'label': Translate('language_%s' % l, language=language)})

        rgtype = db.Query(Bubble).filter('type', 'bubble_type').filter('path', 'reception').get()
        btype = db.Query(Bubble).filter('type', 'bubble_type').filter('path', 'applicant').get()

        self.view(
            language = language,
            main_template='main/print.html',
            template_file = 'application/application.html',
            values = {
                'languages': languages,
                'language': language,
                'bubble': p.GetProperties(language),
                'bubble_key': p.key(),
                'bubble_label': GetDictionaryValue(btype.name, language) if hasattr(btype, 'name') else '',
                'receptions': receptions,
                'receptions_label': GetDictionaryValue(rgtype.name_plural, language) if hasattr(rgtype, 'name_plural') else '',
                'subbubbles': subbubbles,
                'leeching_count': leeching_count,
                'blobstore_upload_url': blobstore.create_upload_url('/application/upload_file'),
            }
        )

    def post(self):
        user = users.get_current_user()
        if user:
            p = db.Query(Bubble).filter('user', user.email()).filter('x_is_deleted', False).get()
            if not p:
                self.redirect('/application/signin')
                return
        else:
            sess = Session(self)
            if 'applicant_key' not in sess:
                return
            p = db.Query(Bubble).filter('type', 'pre_applicant').filter('__key__', db.Key(sess['applicant_key'])).get()
            if not p:
                p = db.Query(Bubble).filter('type', 'applicant').filter('__key__', db.Key(sess['applicant_key'])).get()
            if not p:
                return

        value = p.SetProperty(
            propertykey = self.request.get('property').strip(),
            oldvalue = self.request.get('oldvalue').strip(),
            newvalue = self.request.get('newvalue').strip(),
            user = getattr(p, 'email', ''),
        )
        self.echo(self.request.get('newvalue').strip(), False)


class EditSubmission(boRequestHandler):
    def post(self):
        user = users.get_current_user()
        if user:
            p = db.Query(Bubble).filter('user', user.email()).filter('x_is_deleted', False).get()
            if not p:
                self.redirect('/application/signin')
                return
        else:
            sess = Session(self)
            if 'applicant_key' not in sess:
                return
            p = db.Query(Bubble).filter('type', 'pre_applicant').filter('__key__', db.Key(sess['applicant_key'])).get()
            if not p:
                p = db.Query(Bubble).filter('type', 'applicant').filter('__key__', db.Key(sess['applicant_key'])).get()
            if not p:
                return

        action = self.request.get('action').strip()
        bubblekey = self.request.get('bubble').strip()
        if not bubblekey:
            return

        if action == 'add':
            AddTask('/taskqueue/add_relation', {
                'bubble': str(db.Key(bubblekey)),
                'related_bubble': str(p.key()),
                'type': 'leecher',
                'user': getattr(p, 'email', '')
            }, 'one-by-one')
        else:
            AddTask('/taskqueue/remove_relation', {
                'bubble': str(db.Key(bubblekey)),
                'related_bubble': str(p.key()),
                'type': 'leecher',
                'user': getattr(p, 'email', '')
            }, 'one-by-one')


class EditSubbubble(boRequestHandler):
    def post(self):
        user = users.get_current_user()
        if user:
            p = db.Query(Bubble).filter('user', user.email()).filter('x_is_deleted', False).get()
            if not p:
                self.redirect('/application/signin')
                return
        else:
            sess = Session(self)
            if 'applicant_key' not in sess:
                return
            p = db.Query(Bubble).filter('type', 'pre_applicant').filter('__key__', db.Key(sess['applicant_key'])).get()
            if not p:
                p = db.Query(Bubble).filter('type', 'applicant').filter('__key__', db.Key(sess['applicant_key'])).get()
            if not p:
                return

        bubblekey = self.request.get('bubble').strip()
        if bubblekey:
            bubble = Bubble().get(bubblekey)
        else:
            bt = db.Query(Bubble).filter('type', 'bubble_type').filter('path', self.request.get('type').strip()).get()
            bubble = Bubble()
            bubble.type = bt.path
            bubble.x_type = bt.key()
            bubble.put(getattr(p, 'email', ''))

        AddTask('/taskqueue/add_relation', {
            'bubble': str(p.key()),
            'related_bubble': str(bubble.key()),
            'type': 'subbubble',
            'user': getattr(p, 'email', '')
        }, 'one-by-one')

        value = bubble.SetProperty(
            propertykey = self.request.get('property').strip(),
            oldvalue = self.request.get('oldvalue').strip(),
            newvalue = self.request.get('newvalue').strip(),
            user = getattr(p, 'email', ''),
        )


        # Set rights
        viewers_for_message = []
        for s in db.Query(Bubble).filter('type', 'submission').fetch(1000):
            if getattr(s, 'start_datetime', datetime.now()) < datetime.now() and getattr(s, 'end_datetime', datetime.now()) > datetime.now():
                br = db.Query(BubbleRelation).filter('bubble', s.key()).filter('related_bubble', p.key()).filter('type', 'leecher').filter('x_is_deleted', False).get()
                if br:
                    p.x_br_viewer = s.x_br_viewer
                    p.put(getattr(p, 'email', ''))

                    for sb in Bubble.get(p.x_br_subbubble):
                        if sb.type in ['cv_edu', 'cv_edu_ba', 'cv_edu_ma', 'cv_work', 'state_exam', 'applicant_doc', 'message']:
                            sb.x_br_viewer = s.x_br_viewer
                            sb.put(getattr(p, 'email', ''))
                            viewers_for_message = ListMerge(viewers_for_message, s.x_br_viewer)


        # Send messages
        if self.request.get('oldvalue').strip() != self.request.get('newvalue').strip():
            bt = bubble.GetType()
            alter = bt.GetValueAsList('notify_on_alter')
            if len(alter) > 0:
                message = ''
                for t in bubble.GetProperties():
                    message += '<b>%s</b>:<br/>\n' % t['name']
                    message += '%s<br/>\n' % '<br/>\n'.join(['%s' % n['value'].replace('\n', '<br/>\n') for n in t['values'] if n['value']])
                    message += '<br/>\n'
                for a in alter:
                    for r in [x for x in db.get(viewers_for_message) if x.kind() == 'Bubble']:
                        emails = ListMerge(getattr(r, 'email', []), getattr(r, 'user', []))
                        SendMail(
                            to = emails,
                            subject = Translate('message_notify_on_alter_subject') % bt.displayname.lower(),
                            message = message,
                        )

        self.echo_json({
            'bubble': str(bubble.key()),
            'value': self.request.get('newvalue').strip()
        })


class DownloadFile(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, data_property, file_key=None):
        user = users.get_current_user()
        if user:
            p = db.Query(Bubble).filter('user', user.email()).filter('x_is_deleted', False).get()
            if not p:
                self.redirect('/application/signin')
                return
        else:
            sess = Session(self)
            if 'applicant_key' not in sess:
                return
            p = db.Query(Bubble).filter('type', 'pre_applicant').filter('__key__', db.Key(sess['applicant_key'])).get()
            if not p:
                p = db.Query(Bubble).filter('type', 'applicant').filter('__key__', db.Key(sess['applicant_key'])).get()
            if not p:
                return

        b = blobstore.BlobInfo.get(urllib.unquote(file_key))
        if not b:
            self.error(404)
            return

        bubble = db.Query(Bubble).filter(data_property, b.key()).get()
        if not bubble:
            self.error(404)
            return

        if not bubble.key() in p.GetValueAsList('x_br_subbubble'):
            self.error(404)
            return

        self.send_blob(b, save_as = ReplaceUTF(b.filename))


class UploadFile(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        user = users.get_current_user()
        if user:
            p = db.Query(Bubble).filter('user', user.email()).filter('x_is_deleted', False).get()
            if not p:
                self.redirect('/application/signin')
                return
        else:
            sess = Session(self)
            if 'applicant_key' not in sess:
                return
            p = db.Query(Bubble).filter('type', 'pre_applicant').filter('__key__', db.Key(sess['applicant_key'])).get()
            if not p:
                p = db.Query(Bubble).filter('type', 'applicant').filter('__key__', db.Key(sess['applicant_key'])).get()
            if not p:
                return

        upload_files = self.get_uploads('file')
        if not upload_files:
            return

        blob_info = upload_files[0]

        bubblekey = self.request.get('bubble').strip()

        if bubblekey == str(p.key()):
            value = p.SetProperty(
                propertykey = self.request.get('property').strip(),
                newvalue = blob_info.key(),
                user = getattr(p, 'email', ''),
            )
            if blob_info.content_type in ['image/bmp', 'image/jpeg', 'image/pjpeg', 'image/png', 'image/gif', 'image/tiff', 'image/x-icon']:
                self.response.out.write(images.get_serving_url(blob_info.key()))
        else:
            if bubblekey:
                bubble = Bubble().get(bubblekey)
            else:
                bt = db.Query(Bubble).filter('type', 'bubble_type').filter('path', self.request.get('type').strip()).get()
                bubble = Bubble()
                bubble.type = bt.path
                bubble.x_type = bt.key()
                bubble.put(getattr(p, 'email', ''))

            AddTask('/taskqueue/add_relation', {
                'bubble': str(p.key()),
                'related_bubble': str(bubble.key()),
                'type': 'subbubble',
                'user': getattr(p, 'email', '')
            }, 'one-by-one')

            value = bubble.SetProperty(
                propertykey = self.request.get('property').strip(),
                oldvalue = self.request.get('oldvalue').strip(),
                newvalue = blob_info.key(),
                user = getattr(p, 'email', ''),
            )
            self.response.out.write(simplejson.dumps({
                'filename': blob_info.filename,
                'bubble': str(bubble.key())
            }))

        # Set rights
        for s in db.Query(Bubble).filter('type', 'submission').fetch(1000):
            if getattr(s, 'start_datetime', datetime.now()) < datetime.now() and getattr(s, 'end_datetime', datetime.now()) > datetime.now():
                br = db.Query(BubbleRelation).filter('bubble', s.key()).filter('related_bubble', p.key()).filter('type', 'leecher').filter('x_is_deleted', False).get()
                if br:
                    p.x_br_viewer = s.x_br_viewer
                    p.put(getattr(p, 'email', ''))

                    for sb in Bubble.get(p.x_br_subbubble):
                        if sb.type in ['cv_edu', 'cv_edu_ba', 'cv_edu_ma', 'cv_work', 'state_exam', 'applicant_doc', 'message']:
                            sb.x_br_viewer = s.x_br_viewer
                            sb.put(getattr(p, 'email', ''))


class SelectFieldValues(boRequestHandler):
    def post(self):
        language = self.request.get('language', SystemPreferences().get('default_language')).strip()

        bp = Bubble().get(self.request.get('property').strip())
        if not bp:
            return

        result = []
        if bp.GetValue('data_type') == 'dictionary_select':
            for c in bp.GetValueAsList('choices'):
                for d in sorted(db.Query(Dictionary).filter('name', c).fetch(100), key=attrgetter(language)):
                    result.append({
                        'key': str(d.key()),
                        'value': getattr(d, language)
                    })

        self.echo_json({
            'property': str(bp.key()),
            'values': result
        })


class Submit(boRequestHandler):
    def post(self):
        user = users.get_current_user()
        if user:
            p = db.Query(Bubble).filter('user', user.email()).filter('x_is_deleted', False).get()
            if not p:
                self.redirect('/application/signin')
                return
        else:
            sess = Session(self)
            if 'applicant_key' not in sess:
                return
            p = db.Query(Bubble).filter('type', 'pre_applicant').filter('__key__', db.Key(sess['applicant_key'])).get()
            if not p:
                p = db.Query(Bubble).filter('type', 'applicant').filter('__key__', db.Key(sess['applicant_key'])).get()
            if not p:
                return

        bt = db.Query(Bubble).filter('type', 'bubble_type').filter('path', 'applicant').get()
        p.type = bt.path
        p.x_type = bt.key()
        p.put(getattr(p, 'email', ''))
        p.AutoFix()
        p.ResetCache()

        for s in db.Query(Bubble).filter('type', 'submission').fetch(1000):
            if getattr(s, 'start_datetime', datetime.now()) < datetime.now() and getattr(s, 'end_datetime', datetime.now()) > datetime.now():
                br = db.Query(BubbleRelation).filter('bubble', s.key()).filter('related_bubble', p.key()).filter('type', 'leecher').filter('x_is_deleted', False).get()
                if br:
                    p.x_br_viewer = s.x_br_viewer
                    p.put(getattr(p, 'email', ''))

                    for sb in Bubble.get(p.x_br_subbubble):
                        if sb.type in ['cv_edu', 'cv_edu_ba', 'cv_edu_ma', 'cv_work', 'state_exam', 'applicant_doc', 'message']:
                            sb.x_br_viewer = s.x_br_viewer
                            sb.put(getattr(p, 'email', ''))


class Ratings(boRequestHandler):
    def get(self, bubble_id, person_key):
        language = self.request.get('language', SystemPreferences().get('default_language')).strip()

        try:
            bubble = Bubble().get_by_id(int(bubble_id))
        except Exception, e:
            self.error(404)
            return
        try:
            person = Bubble().get(person_key)
        except Exception, e:
            self.error(404)
            return

        ratingscale = Bubble().get(bubble.rating_scale)
        # Collect all possible grades on scale
        grades = {}
        for g in ratingscale.GetRelatives('subbubble'):
            grades[str(g.key())] = {
                'key': str(g.key()),
                'displayname' : g.displayname,
                'sort': getattr(g, 'x_sort_%s' % UserPreferences().current.language),
                'is_positive': getattr(g, 'is_positive', False),
                'equivalent': getattr(g, 'equivalent', 0),
            }

        # Collect all ratings that match available grades
        ratings = {}
        for r in bubble.GetRelatives('subbubble', 'rating'):
            if r.x_is_deleted == False and getattr(r, 'grade', False) and str(r.grade) in grades:
                ratings[str(r.person)] = grades[str(r.grade)]

        # Collect leechers of bubble
        leechers = {}
        for l in bubble.GetRelatives('leecher'):
            leechers[str(l.key())] = {
                'key': str(l.key()),
                'displayname' : '-',
                'grade': ratings[str(l.key())] if str(l.key()) in ratings else False,
                'equivalent' : 0,
                'is_positive' : ratings[str(l.key())]['is_positive'] if str(l.key()) in ratings else False,
                'ordinal' : 9999999,
            }

        if person_key in leechers.keys():
            leechers[person_key]['displayname'] = person.displayname
        else:
            self.error(404)
            return

        subgrades = {}
        allgrades = {}
        exams = {}
        for exam_bubble in bubble.GetRelatives('subbubble', 'exam'):
            exam_key = str(exam_bubble.key())
            exams[exam_key] = {
                'displayname': exam_bubble.displayname,
            }

            for exam_rating in exam_bubble.GetRelatives('subbubble', 'rating'):
                if exam_rating.x_is_deleted == True:
                    continue
                if str(exam_rating.person) not in leechers:
                    logging.warning('Person ' + str(exam_rating.person) + ' not in leechers of bubble ' + str(bubble.key()))
                    continue
                if not getattr(exam_rating, 'grade', False):
                    logging.warning('Rating ' + str(exam_rating.key()) + ' has no grade')
                    continue
                grade_key = str(exam_rating.grade)
                if grade_key not in allgrades:
                    grade_bubble = Bubble().get(exam_rating.grade)
                    allgrades[grade_key] = {
                        'displayname': grade_bubble.displayname,
                        'is_positive': getattr(grade_bubble, 'is_positive', False),
                        'equivalent': getattr(grade_bubble, 'equivalent', 0),
                    }

                leechers[str(exam_rating.person)]['equivalent'] += allgrades[grade_key]['equivalent']
                leechers[str(exam_rating.person)]['ordinal'] -= getattr(exam_rating, 'ordinal', 0)
                leechers[str(exam_rating.person)]['is_positive'] = False if allgrades[grade_key]['is_positive'] == False else leechers[str(exam_rating.person)]['is_positive']
                subgrades[str(exam_rating.bubble)+str(exam_rating.person)] = {'grade': allgrades[grade_key], 'bubble': exams[exam_key]}

        for bk, bv in exams.iteritems():
            for lk, lv in leechers.iteritems():
                if 'subgrades' not in lv:
                    leechers[lk]['subgrades'] = []
                if bk+lk in subgrades:
                    leechers[lk]['subgrades'].append(subgrades[bk+lk])
                else:
                    leechers[lk]['subgrades'].append('X')

        #logging.debug('Leechers:' + str(leechers))
        leechers = sorted(leechers.values(), key=itemgetter('is_positive', 'equivalent', 'ordinal'), reverse=True)
        order_number = 0
        one_leecher = []
        for leecher in leechers:
            order_number += 1
            if leecher['key'] == person_key:
                one_leecher = [leecher]
                order_str = str(order_number)


        self.view(
            main_template = 'main/print.html',
            template_file =  'action/rating_print.html',
            values = {
                'bubble': bubble,
                'grades': sorted(grades.values(), key=itemgetter('sort')),
                'subbubbles': exams.values(),
                'order_number': order_str + '/' + str(order_number),
                'leechers': one_leecher,
            }
        )


def main():
    Route([
            ('/application/signin', ShowSignin),
            ('/application/leech', EditSubmission),
            ('/application/subbubble', EditSubbubble),
            (r'/application/file/(.*)/(.*)', DownloadFile),
            (r'/application/ratings/(.*)/(.*)', Ratings),
            ('/application/upload_file', UploadFile),
            ('/application/sfv', SelectFieldValues),
            ('/application/submit', Submit),
            ('/application', ShowApplication),
        ])


if __name__ == '__main__':
    main()
