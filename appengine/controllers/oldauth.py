import hashlib
import base64
from random import randint
from datetime import *
from google.appengine.api import users

from bo import *
from database.oldauth import *


class Login(boRequestHandler):
    def get(self):
        if not self.request.get('site'):
            return

        oa = db.Query(OldAuth).filter('site', self.request.get('site').strip()).get()
        if not oa:
            return

        user = users.get_current_user()
        if not user:
            return

        email = user.email()
        domain = email.split('@')[1]

        if domain not in oa.valid_domains:
            self.redirect(oa.url_error % base64.b64encode(email))
            return

        user_key = hashlib.md5(email + (datetime.today() + timedelta(hours=2)).strftime('%Y-%m-%d') + oa.salt).hexdigest()
        key = base64.b64encode(user_key + email)

        self.redirect(oa.url_login % key)


class Logout(boRequestHandler):
    def get(self):
        if self.request.get('site'):
            oa = db.Query(OldAuth).filter('site', self.request.get('site').strip()).get()
            self.redirect(users.create_logout_url(oa.url_logout))


def main():
    Route([
             ('/oldauth', Login),
             ('/oldauth_exit', Logout),
            ])


if __name__ == '__main__':
    main()
