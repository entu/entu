# -*- coding: utf-8 -*-

from tornado.web import RequestHandler
from tornado import locale

import hashlib
import re
import string

from db import *


class myRequestHandler(RequestHandler):
    def render(self, template_name, **kwargs):
        self.require_setting('app_title', 'this application')
        self.require_setting('app_logo_big', 'this application')

        kwargs['app_title'] = self.settings['app_title']
        kwargs['app_logo_big'] = self.settings['app_logo_big']

        RequestHandler.render(self, template_name, **kwargs)

    def forbidden(self):
        self.set_status(403)
        self.write('Nothing to see here!')

    def missing(self):
        self.set_status(404)
        self.write('404')

    def get_current_user(self):
        session_key = self.get_secure_cookie('session')
        if not session_key:
            return
        user_key = hashlib.md5(self.request.remote_ip + self.request.headers.get('User-Agent', None)).hexdigest()
        return myDb().db.get('SELECT user.id, user.language FROM user, user_profile WHERE user_profile.user_id = user.id AND user_profile.session = %s', session_key+user_key)

    def get_user_locale(self):
        self.require_setting('default_language', 'this application')
        if self.current_user:
            return locale.get(self.current_user['language'])
        else:
            return locale.get(self.settings['default_language'])


def toURL(s):
    letters = {'å':'a', 'ä':'a', 'é':'e', 'ö':'o', 'õ':'o', 'ü':'y', 'š':'sh', 'ž':'zh', 'Å':'A', 'Ä':'A', 'É':'E', 'Ö':'O', 'Õ':'O', 'Ü':'Y', 'Š':'SH', 'Ž':'ZH', '/':'-', ' ': '-', '"': '', '_': '-'}
    s = s.encode('utf-8')
    for k, v in letters.iteritems():
        s = s.replace(k, v)
    s = s.lower()
    s = re.sub(r'/[^a-zA-Z0-9]/', '', s)
    s = s.replace('--', '-')
    return s
