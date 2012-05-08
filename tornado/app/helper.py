from tornado.web import RequestHandler
from tornado.options import options
from tornado import locale
from tornado import database

import hashlib


def myDb():
    return database.Connection(
        host        = options.mysql_host,
        database    = options.mysql_database,
        user        = options.mysql_user,
        password    = options.mysql_password,
    )

class myRequestHandler(RequestHandler):
    def get_current_user(self):
        session_key = self.get_secure_cookie('session')
        if not session_key:
            return
        user_key = hashlib.md5(self.request.remote_ip + self.request.headers.get('User-Agent', None)).hexdigest()
        return myDb().get('SELECT id, email, name, picture FROM user_profile WHERE session = %s', session_key+user_key)

    def get_user_locale(self):
        if not self.current_user:
            #return locale.get('en_US')
            return locale.get('fr_FR')

        # if "locale" not in self.current_user.prefs:
        #     # Use the Accept-Language header
        #     return None
        # return self.current_user.prefs["locale"]


