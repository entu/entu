from tornado import auth, web

import hashlib
import base64
from random import randint
from datetime import *

import db
from helper import *


class Login(myRequestHandler):
    """

    """
    @web.authenticated
    def get(self):
        self.require_setting('oldauth_domain', 'old OIS authentication')
        self.require_setting('oldauth_error', 'old OIS authentication')
        self.require_setting('oldauth_key', 'old OIS authentication')
        self.require_setting('oldauth_login', 'old OIS authentication')
        self.require_setting('oldauth_logout', 'old OIS authentication')

        email = self.current_user.email
        if not email:
            return self.redirect(self.settings['oldauth_logout'])

        if email.split('@')[1] != self.settings['oldauth_domain']:
            return self.redirect(self.settings['oldauth_error'] % base64.b64encode(email))

        user_key = hashlib.md5(email + (datetime.today() + timedelta(hours=2)).strftime('%Y-%m-%d') + self.settings['oldauth_key']).hexdigest()
        key = base64.b64encode(user_key + email)

        self.redirect(self.settings['oldauth_login'] % key)


class Logout(myRequestHandler):
    """

    """
    def get(self):
        self.require_setting('oldauth_logout', 'old OIS authentication')

        self.clear_cookie('session')
        self.redirect(self.settings['oldauth_logout'])


handlers = [
    ('/oldauth', Login),
    ('/oldauth_exit', Logout),
]
