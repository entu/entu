# -*- coding: utf-8 -*-

from tornado import web
from tornado import locale

from tornadomail.message import EmailMessage, EmailMultiAlternatives
from tornadomail.backends.smtp import EmailBackend

import hashlib
import re
import random
import string
import base64
import logging
import json
import datetime, time


class myDatabase():
    __app_settings = None

    @property
    def db(self):
        """
        Returns DB connection.

        """
        return self.settings['databases'][self.request.host]

    @property
    def app_settings(self):
        if self.__app_settings:
            return self.__app_settings

        settings = {}
        for preference in self.db.query('SELECT keyname, value FROM app_settings;'):
            settings[preference.keyname] = preference.value
        self.__app_settings = settings
        logging.debug('Loaded app_settings for %s.' % self.request.host)

        return settings


class myUser():
    __user = None
    __session_key = None

    def get_user_by_session_key(self, session_key):
        if not session_key:
            return None

        if self.__user and self.__session_key == session_key:
            return self.__user

        user_key = hashlib.md5(self.request.remote_ip + self.request.headers.get('User-Agent', None)).hexdigest()
        user = self.db.get("""
            SELECT
                property.entity_id AS id,
                user.id AS user_id,
                user.name,
                user.language,
                user.hide_menu,
                user.email,
                IF(user.picture, user.picture, CONCAT('https://secure.gravatar.com/avatar/', MD5(user.email), '?d=wavatar&s=100')) AS picture,
                user.provider,
                user.access_token,
                %s AS session_key
            FROM
                property_definition,
                property,
                entity,
                user
            WHERE property.property_definition_keyname = property_definition.keyname
            AND entity.id = property.entity_id
            AND property.is_deleted = 0
            AND entity.is_deleted = 0
            AND user.email = property.value_string
            AND property_definition.dataproperty = 'user'
            AND user.session = %s
            LIMIT 1;
        """, session_key, session_key+user_key)

        if not user:
            logging.debug('No current user!')
            return

        if not user.id:
            logging.debug('No current user!')
            return

        self.__user = user
        self.__session_key = session_key

        logging.debug('Loaded user #%s' % user.user_id)
        return user

    def set_preferences(self, key, value):
        if key == 'language' and value in ['estonian', 'english']:
            self.db.execute('UPDATE user SET language = %s WHERE id = %s;', value, self.get_current_user().user_id)
        elif key == 'hide_menu' and value.lower() in ['true', 'false']:
            if value.lower() == 'true':
                value = True
            else:
                value = False
            self.db.execute('UPDATE user SET hide_menu = %s WHERE id = %s;', value, self.get_current_user().user_id)

    def user_login(self, session_key=None, provider=None, provider_id=None, email=None, name=None, picture=None, access_token=None):
        """
        Starts session. Creates new (or updates old) user.

        """
        if not session_key:
            session_key = str(''.join(random.choice(string.ascii_letters + string.digits) for x in range(32)) + hashlib.md5(str(time.time())).hexdigest())
        user_key = hashlib.md5(self.request.remote_ip + self.request.headers.get('User-Agent', None)).hexdigest()

        profile_id = self.db.execute_lastrowid('INSERT INTO user SET provider = %s, provider_id = %s, email = %s, name = %s, picture = %s, language = %s, session = %s, access_token = %s, login_count = 0, created = NOW() ON DUPLICATE KEY UPDATE email = %s, name = %s, picture = %s, session = %s, access_token = %s, login_count = login_count + 1, changed = NOW();',
                # insert
                provider,
                provider_id,
                email,
                name,
                picture,
                self.app_settings['default_language'],
                session_key+user_key,
                access_token,
                # update
                email,
                name,
                picture,
                session_key+user_key,
                access_token
            )

        self.set_secure_cookie('session', session_key)

        return session_key

    def user_logout(self, session_key=None):
        """
        Ends user session.

        """
        if self.current_user:
            self.db.execute('UPDATE user SET session = NULL, access_token = NULL WHERE id = %s;', self.current_user.user_id)

        self.clear_cookie('session')


class myRequestHandler(web.RequestHandler, myDatabase, myUser):
    """
    Rewriten tornado.web.RequestHandler methods.

    """
    __timer_start = None
    __timer_last = None
    __request_id = None

    def prepare(self):
        self.__request_id = self.db.execute_lastrowid('INSERT INTO app_requests SET date = NOW(), port = %s, method = %s, url = %s, arguments = %s, user_id = %s, ip = %s, browser = %s;',
            self.settings['port'],
            self.request.method,
            self.request.full_url(),
            str(self.request.arguments) if self.request.arguments else None,
            self.get_current_user().id if self.get_current_user() else None,
            self.request.remote_ip,
            self.request.headers.get('User-Agent', None)
        )

    def on_finish(self):
        request_time = self.request.request_time()

        if request_time > (float(self.settings['slow_request_ms'])/1000.0):
            self.settings['slow_request_count'] += 1
            self.settings['slow_request_time'] += request_time
            logging.warning('%s %s request time was %0.3fs!' % (self.request.method, self.request.full_url(), round(request_time, 3)))
        else:
            self.settings['request_count'] += 1
            self.settings['request_time'] += request_time

        if self.__request_id:
            self.db.execute('UPDATE app_requests SET time = %s, status = %s WHERE id = %s;',
                request_time,
                self.get_status(),
                self.__request_id
            )

    def timer(self, msg=''):
        logging.debug('TIMER: %0.3f - %s' % (round(self.request.request_time(), 3), msg))


    def get_current_user(self):
        """
        Sets and returns logged in user. Properties are, id (Entity ID!), name, language, email, picture. If picture is not set returns gravatar.com picture url.

        """
        return self.get_user_by_session_key(self.get_secure_cookie('session'))

    def get_user_locale(self):
        """
        Sets and returns logged in user locale.

        """
        if self.current_user:
            return locale.get(self.current_user['language'])
        else:
            return locale.get(self.app_settings['default_language'])

    def render(self, template_name, **kwargs):
        """
        Includes app title, logo etc to template and renders it.

        """
        kwargs['app_title'] = self.app_settings['app_title']
        kwargs['app_organisation'] = self.app_settings['app_organisation']
        kwargs['app_logo_big'] = self.app_settings['app_logo_big']
        kwargs['page_title'] = '%s - %s' % (self.app_settings['app_title'], kwargs['page_title']) if kwargs.get('page_title', None) else self.app_settings['app_title']
        kwargs['google_analytics_code'] = self.app_settings['google_analytics_code'] if self.app_settings.get('google_analytics_code') else None

        web.RequestHandler.render(self, template_name, **kwargs)

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
        self.render('main/template/404.html',
            page_title = '404'
        )

    def mail_send(self, to, cc=None, bcc=None, subject='', message='', attachments=None):
        """
        Sends email using GMail account. email_address and gmail_password application settings are required.

        """

        def _finish(num):
            logging.debug('_finish %s' % num)

        if type(to) is not list:
            to = StrToList(to)

        message = EmailMessage(
            subject = subject,
            body = message,
            from_email = self.app_settings['email_address'],
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
        return EmailBackend(
            self.app_settings['email_smtp_server'],
            int(self.app_settings['email_smtp_port']),
            self.app_settings['email_address'],
            swapCrypt(self.app_settings['email_secret']),
            True
        )


class JSONDateFix(json.JSONEncoder):
    """
    Formats json.dumps() datetime values to YYYY-MM-DD HH:MM:SS. Use it like json.dumps(mydata, cls=JSONDateFix)

    """
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return time.strftime('%Y-%m-%d %H:%M:%S', obj.timetuple())
        return json.JSONEncoder.default(self, obj)


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


def GetHumanReadableBytes(size, precision = 2):
    size = int(size)

    suffixes = ['B','KB','MB','GB','TB']
    suffixIndex = 0
    while size >= 1000:
        suffixIndex += 1 #increment the index of the suffix
        size = size / 1000.0 #apply the division

    return '%.*f%s' % (precision, size, suffixes[suffixIndex])
