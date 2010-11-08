import hashlib
import base64
from datetime import date

from bo import *
from database.oldauth import *


class Login(webapp.RequestHandler):
    def get(self):
        if self.request.get('site'):

            u = User().current()

            user = users.get_current_user()
            site = self.request.get('site')
            oa = db.Query(OldAuth).filter('site', site).get()
            if not oa:
                oa = OldAuth()
                oa.site = site
                oa.put()
            user_name = user.nickname()
            user_key = hashlib.md5(user.nickname() + date.today().strftime('%Y-%m-%d') + oa.salt).hexdigest()
            key = base64.b64encode(user_key + user_name)
            if oa.loginurl:
                self.redirect(oa.loginurl % key)


class Logout(webapp.RequestHandler):
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