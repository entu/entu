import hashlib
import base64
from random import randint
from datetime import *

from bo import *
from database.person import *
from database.oldauth import *


class Login(boRequestHandler):
    def get(self):
        if self.authorize():
            if self.request.get('site'):
                p = Person().current
                site = self.request.get('site')
                oa = db.Query(OldAuth).filter('site', site).get()
                if not oa:
                    oa = OldAuth()
                    oa.site = site
                    oa.put()
                user_key = hashlib.md5(p.user + (datetime.today() + timedelta(hours=2)).strftime('%Y-%m-%d') + oa.salt).hexdigest()
                key = base64.b64encode(user_key + p.user)

                if oa.loginurl:
                    self.redirect(oa.loginurl % key)


class Logout(boRequestHandler):
    def get(self):
        if self.request.get('site'):
            user = users.get_current_user()
            site = self.request.get('site')
            oa = db.Query(OldAuth).filter('site', site).get()
            if oa:
                self.redirect(users.create_logout_url(oa.logouturl))


def main():
    Route([
             ('/oldauth', Login),
             ('/oldauth_exit', Logout),
            ])


if __name__ == '__main__':
    main()