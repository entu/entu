from google.appengine.api import users

import urllib
import hashlib
from time import time
from random import random

from bo import *


class OpenIdLoginHandler(webapp.RequestHandler):
    def get(self):
        continue_url = self.request.GET.get('continue')
        openid_url = self.request.GET.get('openid')

        if continue_url:
            continue_url = continue_url.encode('utf8')
        else:
            continue_url = ''

        if not openid_url:
            View(self, 'login', TEMPLATE_LOGIN, { 'continue': continue_url })
        else:
            self.redirect(users.create_login_url(continue_url, None, openid_url))


class RedirectActivate(webapp.RequestHandler):
    def get(self, url):
        self.redirect(users.create_logout_url('/user/activate' + urllib.unquote(url).decode('utf8')))


class NewUserRegistration(webapp.RequestHandler):
    def post(self):
        email = self.request.POST.get('email')

        if email:
            key = hashlib.md5(str(time() * random()) + email).hexdigest()
            link = SYSTEM_URL + '/login/activate/' + email + '/' + key

            u = db.Query(User).filter('email =', email).get()
            if not u:
                u = User()
                u.email = email
            u.activation_key = key
            u.save()

            SendMail(
                to = email,
                subject = Translate('activation_subject'),
                message = Translate('activation_email') % link
            )

            self.response.out.write(Translate('registration_sent') % email)


def main():
    Route([
        (r'/_ah/login_required', OpenIdLoginHandler),
        (r'/login/activate(.*)', RedirectActivate),
        (r'/login/new', NewUserRegistration),
    ])


if __name__ == '__main__':
    main()