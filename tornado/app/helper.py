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
        user = myDb().db.get("""
            SELECT
            property.bubble_id AS id,
            user.name,
            user.language,
            user.email,
            user.picture
            FROM
            property_definition,
            property,
            user,
            user_profile
            WHERE property.property_definition_id = property_definition.id
            AND user.email = property.value_string
            AND user_profile.user_id = user.id
            AND property_definition.dataproperty = 'user'
            AND user_profile.session = %s
        """, session_key+user_key)

        if not user:
            return

        if not user.picture:
            user.picture = 'http://www.gravatar.com/avatar/%s?d=monsterid' % (hashlib.md5(user.email).hexdigest())
            user['picture'] = user.picture

        return user

    def get_user_locale(self):
        self.require_setting('default_language', 'this application')
        if self.current_user:
            return locale.get(self.current_user['language'])
        else:
            return locale.get(self.settings['default_language'])


def toURL(s):
    letters = {'å':'a', 'ä':'a', 'é':'e', 'ö':'o', 'õ':'o', 'ü':'y', 'š':'sh', 'ž':'zh', 'Å':'A', 'Ä':'A', 'É':'E', 'Ö':'O', 'Õ':'O', 'Ü':'Y', 'Š':'SH', 'Ž':'ZH', ' ':'-', '_':'-', '/':'-'}
    s = s.encode('utf-8')
    for k, v in letters.iteritems():
        s = s.replace(k, v)
    s = s.replace(' ', '-')
    s = s.lower()
    s = re.sub(r'[^-a-zA-Z0-9]', '', s)
    s = s.replace('--', '-').replace('--', '-').replace('--', '-')
    return s
