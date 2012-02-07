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
from database.person import *
from django.utils import simplejson

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
                p = db.Query(Bubble).filter('type', 'applicant').filter('email', email).get()
                if not p:
                    p = db.Query(Bubble).filter('users', email).get()
                    if not p:
                        p = Bubble()
                        p.type = 'applicant'
                        p.email = email
                        p.put(email)

                password = ''.join(random.choice(string.ascii_letters) for x in range(2))
                password += str(p.key().id())
                password += ''.join(random.choice(string.ascii_letters) for x in range(3))
                password = password.replace('O', random.choice(string.ascii_lowercase))

                p.language = language
                p.password = password
                p.put(getattr(p, 'email', ''))

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
        language = self.request.get('language', SystemPreferences().get('default_language')).strip()

        user = users.get_current_user()
        if user:
            p = db.Query(Bubble).filter('users', user.email()).filter('_is_deleted', False).get()
            if not p:
                self.redirect('/application/signin')
                return
            if p.type != 'applicant':
                p.type = 'applicant'
                p.put()
        else:
            sess = Session(self, timeout=86400)
            if 'applicant_key' not in sess:
                self.redirect('/application/signin')
                return
            p = db.Query(Bubble).filter('type', 'applicant').filter('__key__', db.Key(sess['applicant_key'])).get()
            if not p:
                self.redirect('/application/signin')
                return

        if getattr(p, 'language', '') != language:
            p.language = language
            p.put()

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
        for t in ['cv_edu', 'cv_work', 'state_exam', 'applicant_doc', 'message']:
            props = []
            for b in sorted(Bubble.get(p.optional_bubbles), key=attrgetter('_created')):
                if b:
                    if b.type == t and b._is_deleted == False:
                        props.append({'key': str(b.key()), 'props': b.GetProperties(language)})
            eb = Bubble()
            eb.type = t
            eb._created = None
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
                'bubble_key': p.key(),
                'bubble_label': getattr(btype.name, language),
                'receptions': receptions,
                'receptions_label': getattr(rgtype.name_plural, language),
                'subbubbles': subbubbles,
                'leeching_count': leeching_count,
                'blobstore_upload_url': blobstore.create_upload_url('/application/upload_file'),
            }
        )

    def post(self):
        user = users.get_current_user()
        if user:
            p = db.Query(Bubble).filter('users', user.email()).filter('_is_deleted', False).get()
            if not p:
                self.redirect('/application/signin')
                return
        else:
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
            user = getattr(p, 'email', ''),
        )
        self.echo(self.request.get('newvalue').strip(), False)


class EditSubmission(boRequestHandler):
    def post(self):
        user = users.get_current_user()
        if user:
            p = db.Query(Bubble).filter('users', user.email()).filter('_is_deleted', False).get()
            if not p:
                self.redirect('/application/signin')
                return
        else:
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
            br.put(getattr(p, 'email', ''))
        else:
            if br:
                br._is_deleted = True
                br.put(getattr(p, 'email', ''))


class EditSubbubble(boRequestHandler):
    def post(self):
        user = users.get_current_user()
        if user:
            p = db.Query(Bubble).filter('users', user.email()).filter('_is_deleted', False).get()
            if not p:
                self.redirect('/application/signin')
                return
        else:
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
            bubble.put(getattr(p, 'email', ''))
            p.optional_bubbles = AddToList(bubble.key(), p.optional_bubbles)
            p.put(getattr(p, 'email', ''))

        value = bubble.SetProperty(
            propertykey = self.request.get('property').strip(),
            oldvalue = self.request.get('oldvalue').strip(),
            newvalue = self.request.get('newvalue').strip(),
            user = getattr(p, 'email', ''),
        )

        self.echo_json({
            'bubble': str(bubble.key()),
            'value': self.request.get('newvalue').strip()
        })


class DownloadFile(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, data_property, file_key=None):
        user = users.get_current_user()
        if user:
            p = db.Query(Bubble).filter('users', user.email()).filter('_is_deleted', False).get()
            if not p:
                self.redirect('/application/signin')
                return
        else:
            sess = Session(self, timeout=86400)
            if 'applicant_key' not in sess:
                return
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

        if not bubble.key() in p.optional_bubbles:
            self.error(404)
            return

        self.send_blob(b, save_as = ReplaceUTF(b.filename))


class UploadFile(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        user = users.get_current_user()
        if user:
            p = db.Query(Bubble).filter('users', user.email()).filter('_is_deleted', False).get()
            if not p:
                self.redirect('/application/signin')
                return
        else:
            sess = Session(self, timeout=86400)
            if 'applicant_key' not in sess:
                return
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
                bubble = Bubble()
                bubble.type = self.request.get('type').strip()
                bubble.put(getattr(p, 'email', ''))
                p.optional_bubbles = AddToList(bubble.key(), p.optional_bubbles)
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


class Submit(boRequestHandler):
    def post(self):
        user = users.get_current_user()
        if user:
            p = db.Query(Bubble).filter('users', user.email()).filter('_is_deleted', False).get()
            if not p:
                self.redirect('/application/signin')
                return
        else:
            sess = Session(self, timeout=86400)
            if 'applicant_key' not in sess:
                return
            p = db.Query(Bubble).filter('type', 'applicant').filter('__key__', db.Key(sess['applicant_key'])).get()
            if not p:
                return

        for s in db.Query(Bubble).filter('type', 'submission').fetch(1000):
            # if getattr(s, 'start_datetime', datetime.now()) < datetime.now() and getattr(s, 'end_datetime', datetime.now()) > datetime.now():
            if getattr(s, 'start_date', datetime.now()) < datetime.now() and getattr(s, 'end_date', datetime.now()) > datetime.now():
                br = db.Query(BubbleRelation).filter('bubble', s.key()).filter('related_bubble', p.key()).filter('type', 'leecher').filter('_is_deleted', False).get()
                if br:
                    p.viewers = s.viewers
                    p.put(getattr(p, 'email', ''))

                    for sb in Bubble.get(p.optional_bubbles):
                        if sb.type in ['cv_edu', 'cv_work', 'state_exam', 'applicant_doc', 'message']:
                            sb.viewers = s.viewers
                            sb.put(getattr(p, 'email', ''))



def main():
    Route([
            ('/application/signin', ShowSignin),
            ('/application/leech', EditSubmission),
            ('/application/subbubble', EditSubbubble),
            (r'/application/file/(.*)/(.*)', DownloadFile),
            ('/application/upload_file', UploadFile),
            ('/application/submit', Submit),
            ('/application', ShowApplication),
        ])


if __name__ == '__main__':
    main()
