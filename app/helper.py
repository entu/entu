# -*- coding: utf-8 -*-

from tornado.web import RequestHandler
from tornado import locale

from tornadomail.message import EmailMessage, EmailMultiAlternatives
from tornadomail.backends.smtp import EmailBackend

import hashlib
import re
import string
import base64
import logging


import db


class myRequestHandler(RequestHandler):
    """
    Rewriten tornado.web.RequestHandler methods.

    """

    session_key = None

    def render(self, template_name, **kwargs):
        """
        Includes app title, logo etc to template and renders it.

        """
        self.require_setting('app_title', 'this application')
        self.require_setting('app_organisation', 'this application')
        self.require_setting('app_logo_big', 'this application')

        kwargs['app_title'] = self.settings['app_title']
        kwargs['app_organisation'] = self.settings['app_organisation']
        kwargs['app_logo_big'] = self.settings['app_logo_big']
        kwargs['page_title'] = '%s - %s' % (self.settings['app_title'], kwargs['page_title']) if kwargs.get('page_title', None) else self.settings['app_title']
        kwargs['google_analytics_code'] = self.settings['google_analytics_code'] if 'google_analytics_code' in self.settings else None

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
        if not self.session_key:
            self.session_key = self.get_secure_cookie('session')

        if not self.session_key:
            return

        return self.get_user_by_session_key(self.session_key)

    def get_user_by_session_key(self, session_key):

        if not session_key:
            return None

        user_key = hashlib.md5(self.request.remote_ip + self.request.headers.get('User-Agent', None)).hexdigest()
        user = db.User(session=session_key+user_key)

        if not user.id:
            return None

        if not user.picture:
            user.picture = 'https://secure.gravatar.com/avatar/%s?d=wavatar&s=100' % (hashlib.md5(user.email).hexdigest())
            user['picture'] = user.picture
            user['session_key'] = self.session_key

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

    def mail_send(self, to, cc=None, bcc=None, subject='', message='', attachments=None):
        """
        Sends email using GMail account. email_address and gmail_password application settings are required.

        """
        self.require_setting('email_address', 'email sending')

        def _finish(num):
            logging.debug('_finish %s' % num)

        if type(to) is not list:
            to = StrToList(to)

        message = EmailMessage(
            subject = subject,
            body = message,
            from_email = self.settings['email_address'],
            to = to,
            cc = cc,
            bcc = bcc,
            connection = self.__mail_connection
        )

        # message.attach(
        #     filename = '',
        #     content = ''
        # )

        message.send(callback=_finish)

    @property
    def __mail_connection(self):
        self.require_setting('email_smtp_server', 'email sending')
        self.require_setting('email_smtp_port', 'email sending')
        self.require_setting('email_address', 'email sending')
        self.require_setting('email_secret', 'email sending')

        return EmailBackend(
            self.settings['email_smtp_server'],
            int(self.settings['email_smtp_port']),
            self.settings['email_address'],
            swapCrypt(self.settings['email_secret']),
            True
        )


def swapCrypt(s, encrypt=False):
    """
    This function will encrypt/decrypt a string.

    """
    if not encrypt:
        s = base64.b64decode(s)
    list1 = list(s)
    for k in range(0, len(list1), 2):
        if len(list1) > k + 1:
            list1[k], list1[k+1] = list1[k+1], list1[k]
    if not encrypt:
        return ''.join(list1)
    return base64.b64encode(''.join(list1))


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


def toDecimal(s=None):
    if not s:
        return 0.0
    if type(s) is float:
        return s
    if type(s) is int:
        return float(s)
    result = s.replace(',', '.')
    result = re.sub(r'[^\.0-9: ]', '', result)
    if not result:
        return 0.0
    result = float(result)
    return result


def checkEmail(email):
    if re.match('[^@]+@[^@]+\.[^@]+', email):
        return True


def StrToList(string):
    if not string:
        return []
    return [x.strip() for x in string.strip().replace('\n', ' ').replace(',', ' ').replace(';', ' ').split(' ') if len(x.strip()) > 0]


def ListMatch(l1 = None, l2 = None):
    # ListMatch(['a', 'b', 'c', 'd'], ['b', 'e', 'a']) = ['a', 'b']
    if not l1 or not l2:
        return []
    if type(l1) is not list:
        l1 = [l1]
    if type(l2) is not list:
        l2 = [l2]
    l = set(l1)
    return list(l.intersection(l2))
