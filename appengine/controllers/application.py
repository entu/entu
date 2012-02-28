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

                for k in ['agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUY4PvbAgw', 'agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYwLLLAgw', 'agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYyvrLAgw', 'agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUY1IfMAgw', 'agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYy_rLAgw']:
                    AddTask('/taskqueue/rights', {
                        'bubble': str(p.key()),
                        'person': str(db.Key(k)),
                        'right': 'viewer',
                        'user': getattr(p, 'email', '')
                    }, 'bubble-one-by-one')

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
                p.type = 'applicant'
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
            setattr(p, 'x_br_viewer', MergeLists(p.key(), p.GetValueAsList('x_br_viewer')))
            p.put()

        receptions = []
        leeching_count = 0
        for g in sorted(db.Query(Bubble).filter('type', 'reception_group').fetch(1000), key=attrgetter('x_sort_%s' % language)):
            gname = getattr(Dictionary.get(g.name), language)
            gname2 = ''
            for r in sorted(db.Query(Bubble).filter('type', 'reception').filter('__key__ IN', g.GetValueAsList('x_br_subbubble')).fetch(1000), key=attrgetter('x_sort_%s' % language)):
                for s in sorted(db.Query(Bubble).filter('type', 'submission').filter('__key__ IN', r.GetValueAsList('x_br_subbubble')).fetch(1000), key=attrgetter('x_sort_%s' % language)):
                    if getattr(s, 'start_datetime', datetime.now()) < datetime.now() and getattr(s, 'end_datetime', datetime.now()) > datetime.now():
                        br = db.Query(BubbleRelation).filter('bubble', s.key()).filter('related_bubble', p.key()).filter('type', 'leecher').filter('x_is_deleted', False).get()
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
        for t in ['cv_edu', 'cv_work', 'state_exam', 'applicant_doc', 'message']:
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

        br = db.Query(BubbleRelation).filter('bubble', db.Key(bubblekey)).filter('related_bubble', p.key()).filter('type', 'leecher').get()
        if action == 'add':
            if br:
                br.x_is_deleted = False
            else:
                br = BubbleRelation()
                br.type = 'leecher'
                br.bubble = db.Key(bubblekey)
                br.related_bubble = p.key()
            br.put(getattr(p, 'email', ''))
        else:
            if br:
                br.x_is_deleted = True
                br.put(getattr(p, 'email', ''))


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
            p.x_br_subbubble = AddToList(bubble.key(), p.GetValueAsList('x_br_subbubble'))
            p.put(getattr(p, 'email', ''))

        value = bubble.SetProperty(
            propertykey = self.request.get('property').strip(),
            oldvalue = self.request.get('oldvalue').strip(),
            newvalue = self.request.get('newvalue').strip(),
            user = getattr(p, 'email', ''),
        )

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
                    for r in bubble.GetRelatives(a):
                        emails = MergeLists(getattr(r, 'email', []), getattr(r, 'user', []))
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
                p.x_br_subbubble = AddToList(bubble.key(), p.GetValueAsList('x_br_subbubble'))
                p.put(getattr(p, 'email', ''))

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

        for s in db.Query(Bubble).filter('type', 'submission').fetch(1000):
            if getattr(s, 'start_datetime', datetime.now()) < datetime.now() and getattr(s, 'end_datetime', datetime.now()) > datetime.now():
                br = db.Query(BubbleRelation).filter('bubble', s.key()).filter('related_bubble', p.key()).filter('type', 'leecher').filter('x_is_deleted', False).get()
                if br:
                    p.x_br_viewer = s.x_br_viewer
                    p.put(getattr(p, 'email', ''))

                    for sb in Bubble.get(p.x_br_subbubble):
                        if sb.type in ['cv_edu', 'cv_work', 'state_exam', 'applicant_doc', 'message']:
                            sb.x_br_viewer = s.x_br_viewer
                            sb.put(getattr(p, 'email', ''))


def main():
    Route([
            ('/application/signin', ShowSignin),
            ('/application/leech', EditSubmission),
            ('/application/subbubble', EditSubbubble),
            (r'/application/file/(.*)/(.*)', DownloadFile),
            ('/application/upload_file', UploadFile),
            ('/application/sfv', SelectFieldValues),
            ('/application/submit', Submit),
            ('/application', ShowApplication),
        ])


if __name__ == '__main__':
    main()
