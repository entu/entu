# -*- coding: utf-8 -*-

from tornado.web import RequestHandler
from tornado import locale

import hashlib
import re
import string

import db


class myRequestHandler(RequestHandler):
    """
    Rewriten tornado.web.RequestHandler methods.

    """
    def render(self, template_name, **kwargs):
        """
        Includes app title, logo etc to template and renders it.

        """
        self.require_setting('app_title', 'this application')
        self.require_setting('app_logo_big', 'this application')

        kwargs['app_title'] = self.settings['app_title']
        kwargs['app_logo_big'] = self.settings['app_logo_big']

        RequestHandler.render(self, template_name, **kwargs)

    def forbidden(self):
        """
        Show 403 (forbidden) error to user.

        """
        self.set_status(403)
        self.write('Nothing to see here!')

    def missing(self):
        """
        Show 404 (page not found) error to user.

        """
        self.set_status(404)
        self.write('Page not found!')

    def get_current_user(self):
        """
        Sets and returns logged in user. Properties are, id (Entity ID!), name, language, email, picture. If picture is not set returns gravatar.com picture url.

        """
        session_key = self.get_secure_cookie('session')
        if not session_key:
            return
        user_key = hashlib.md5(self.request.remote_ip + self.request.headers.get('User-Agent', None)).hexdigest()

        user = db.User(session_key+user_key)

        if user.is_guest == True:
            return

        if not user.picture:
            user.picture = 'http://www.gravatar.com/avatar/%s?d=monsterid' % (hashlib.md5(user.email).hexdigest())
            user['picture'] = user.picture

        return user

    def get_user_locale(self):
        """
        Sets and returns logged in user locale.

        """
        self.require_setting('default_language', 'this application')
        if self.current_user:
            return locale.get(self.current_user['language'])
        else:
            return locale.get(self.settings['default_language'])


def toURL(s):
    """
    Converts string to lowercase ascii only url.

    """
    letters = {'å':'a', 'ä':'a', 'é':'e', 'ö':'o', 'õ':'o', 'ü':'y', 'š':'sh', 'ž':'zh', 'Å':'A', 'Ä':'A', 'É':'E', 'Ö':'O', 'Õ':'O', 'Ü':'Y', 'Š':'SH', 'Ž':'ZH', ' ':'-', '_':'-', '/':'-'}
    s = s.encode('utf-8')
    for k, v in letters.iteritems():
        s = s.replace(k, v)
    s = s.replace(' ', '-')
    s = s.lower()
    s = re.sub(r'[^-a-zA-Z0-9]', '', s)
    s = s.replace('--', '-').replace('--', '-').replace('--', '-')
    return s


def FindTags(s, beginning, end):
    """
    Finds and returns list of tags from string.

    """
    if not s:
        return []
    return re.compile('%s(.*?)%s' % (beginning, end), re.DOTALL).findall(s)
