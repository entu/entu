# -*- coding: utf-8 -*-

import torndb
from tornado import web
from tornado import locale
from tornado import httpclient

import hmac
import hashlib
import re
import random
import string
import urllib
from SimpleAES import SimpleAES

import logging
import json
import datetime, time
import dateutil.parser


class myDatabase():
    __app_settings = None

    @property
    def db(self):
        """
        Returns current hosts DB connection.

        """
        return self.get_db(self.request.host)

    def get_db(self, host):
        """
        Returns DB connection.

        """
        try:
            x = self.settings['databases'][host].get('SELECT 1 FROM DUAL;')
        except Exception:
            settings = self.get_app_settings(host)
            self.settings['databases'][host] = torndb.Connection(
                host     = settings.get('database-host'),
                database = settings.get('database-name'),
                user     = settings.get('database-user'),
                password = settings.get('database-password'),
            )
        return self.settings['databases'][host]

    def app_settings(self, key, default=None, do_something_fun=False):
        if self.get_app_settings():
            return self.get_app_settings().get(key, default)

        # if not do_something_fun:
        #     return self.get_app_settings().get(key, default)
        # try:
        #     s = self.get_app_settings().get(key)
        #     return SimpleAES('%s.%s' % (self.settings['secret'], self.app_settings('database-name'))).decrypt('\n'.join(s[pos:pos+64] for pos in xrange(0, len(s), 64))).strip()
        # except Exception:
        #     return default

    def get_app_settings(self, host=None):
        if not host:
            host = self.request.host

        if not self.__app_settings:
            logging.debug('Loaded app_settings for %s.' % host)

            db = torndb.Connection(
                host     = self.settings['database-host'],
                database = self.settings['database-database'],
                user     = self.settings['database-user'],
                password = self.settings['database-password'],
            )
            sql = """
                SELECT DISTINCT
                    e.id AS entity,
                    property_definition.dataproperty AS property,
                    IF(
                        property_definition.datatype='decimal',
                        property.value_decimal,
                        IF(
                            property_definition.datatype='integer',
                            property.value_integer,
                            IF(
                                property_definition.datatype='file',
                                property.value_file,
                                IF(
                                    property_definition.datatype='text',
                                    property.value_text,
                                    property.value_string
                                )
                            )
                        )
                    ) AS value
                FROM (
                    SELECT
                        entity.id,
                        entity.entity_definition_keyname
                    FROM
                        entity,
                        relationship
                    WHERE relationship.related_entity_id = entity.id
                    AND entity.is_deleted = 0
                    AND relationship.is_deleted = 0
                    AND relationship.relationship_definition_keyname = 'child'
                    AND relationship.entity_id IN (%s)
                ) AS e
                LEFT JOIN property_definition ON property_definition.entity_definition_keyname = e.entity_definition_keyname AND property_definition.is_deleted = 0
                LEFT JOIN property ON property.property_definition_keyname = property_definition.keyname AND property.entity_id = e.id AND property.is_deleted = 0;
            """ % self.settings['customergroup']
            customers = {}
            for c in db.query(sql):
                customers.setdefault(c.entity, {})[c.property] = c.value

            self.__app_settings = {}
            for c in customers.values():
                self.__app_settings[c.get('domain', '')] = c

        if not self.__app_settings.get(host):
            self.redirect('https://www.entu.ee')
            return

        return self.__app_settings.get(host, {})


class myUser():
    __user        = None
    __session_key = None
    __user_id     = None
    __policy      = None
    __signature   = None

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
                user.provider,
                user.access_token,
                user.session_key,
                NULL AS api_key
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
            AND user.session_key = %s
            AND user.user_key = %s
            LIMIT 1;
        """, session_key, user_key)

        if not user:
            logging.debug('No current user!')
            return

        if not user.id:
            logging.debug('No user id!')
            return

        self.__user = user
        self.__session_key = session_key

        logging.debug('Loaded user #%s' % user.id)
        return user

    def get_user_by_signature(self):
        user_id = self.get_argument('user', default=None, strip=True)
        policy = self.get_argument('policy', default=None, strip=True)
        signature = self.get_argument('signature', default=None, strip=True)

        if self.__user and self.__user_id == user_id and self.__policy == policy and  self.__signature == signature:
            return self.__user

        # encoded_policy = json.dumps({
        #     'expiration': (datetime.datetime.utcnow()+datetime.timedelta(minutes=5)).strftime('%Y-%m-%dT%H:%M:%SZ'),
        #     'conditions': []
        # }).encode('utf-8').encode('base64').replace('\n','')
        # logging.debug(encoded_policy)

        try:
            policy_dict = json.loads(policy.decode('base64').decode('utf-8'))
        except Exception:
            logging.debug('Invalid policy!')
            return

        if 'expiration' not in policy_dict:
            logging.debug('No expiration date!')
            return

        try:
            expiration_time = time.mktime(dateutil.parser.parse(policy_dict['expiration']).timetuple())
        except Exception:
            logging.debug('Invalid expiration date!')
            return

        if time.time() > expiration_time:
            logging.debug('URL is expired!')
            return

        if expiration_time - time.time() > 3600:
            logging.debug('Expiration time must be less than 1 hour!')
            return

        user = self.db.get("""
            SELECT
                entity.id,
                NULL AS user_id,
                NULL AS name,
                'estonian' AS language,
                NULL AS hide_menu,
                NULL AS email,
                NULL AS provider,
                NULL AS access_token,
                NULL AS session_key,
                property.value_string AS api_key
            FROM
                property_definition,
                property,
                entity
            WHERE property.property_definition_keyname = property_definition.keyname
            AND entity.id = property.entity_id
            AND property.is_deleted = 0
            AND entity.is_deleted = 0
            AND property_definition.dataproperty = 'entu-api-key'
            AND entity.id = %s
            LIMIT 1;
        """, user_id)

        if not user:
            logging.debug('No current user!')
            return

        if not user.api_key:
            logging.debug('No user API key!')
            return

        correct_signature = hmac.new(user.api_key.encode('utf-8'), policy.encode('utf-8'), hashlib.sha1).digest().encode('base64').replace('\n','')
        if signature != correct_signature:
            logging.debug('Wrong signature!')
            return

        self.__user = user
        self.__user_id = user_id
        self.__policy = policy
        self.__signature = signature

        logging.debug('Loaded user #%s' % user.id)
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

    def user_login(self, provider=None, provider_id=None, email=None, name=None, picture=None, access_token=None, redirect_url=None):
        """
        Starts session. Creates new (or updates old) user.

        """
        redirect_key = str(''.join(random.choice(string.ascii_letters + string.digits) for x in range(32)) + hashlib.md5(str(time.time())).hexdigest())
        session_key = str(''.join(random.choice(string.ascii_letters + string.digits) for x in range(32)) + hashlib.md5(str(time.time())).hexdigest())
        user_key = hashlib.md5(self.request.remote_ip + self.request.headers.get('User-Agent', None)).hexdigest()
        host = None

        if redirect_url:
            host = redirect_url.replace('http://', '').replace('https://', '').split('/')[0]

        if host:
            db = self.get_db(host)
        else:
            db = self.db

        profile_id = db.execute_lastrowid('INSERT INTO user SET provider = %s, provider_id = %s, email = %s, name = %s, picture = %s, language = %s, session_key = %s, user_key = %s, access_token = %s, redirect_url = %s, redirect_key = %s, login_count = 0, created = NOW() ON DUPLICATE KEY UPDATE email = %s, name = %s, picture = %s, session_key = %s, user_key = %s, access_token = %s, redirect_url = %s, redirect_key = %s, login_count = login_count + 1, changed = NOW();',
                # insert
                provider,
                provider_id,
                email,
                name,
                picture,
                self.app_settings('language', 'english'),
                session_key,
                user_key,
                access_token,
                redirect_url,
                redirect_key,
                # update
                email,
                name,
                picture,
                session_key,
                user_key,
                access_token,
                redirect_url,
                redirect_key
            )

        return {'id': profile_id, 'host': host, 'redirect_key': redirect_key}

    def user_login_redirect(self, profile_id=None, redirect_key=None):
        if not redirect_key or not profile_id:
            return self.redirect('/')

        user = self.db.get('SELECT session_key, redirect_url FROM user WHERE id = %s AND redirect_key = %s LIMIT 1;', profile_id, redirect_key)
        if not user:
            return self.redirect('/')

        self.db.execute('UPDATE user SET redirect_url = NULL, redirect_key = NULL WHERE id = %s AND redirect_key = %s;', profile_id, redirect_key)

        self.clear_cookie('session')
        self.set_secure_cookie('session', user.session_key)
        self.redirect(user.redirect_url)


    def user_logout(self, session_key=None):
        """
        Ends user session.

        """
        if self.current_user:
            self.db.execute('UPDATE user SET session_key = NULL, user_key = NULL, access_token = NULL, redirect_url = NULL, redirect_key = NULL WHERE id = %s;', self.current_user.user_id)

        self.clear_cookie('session')


class myRequestHandler(web.RequestHandler, myDatabase, myUser):
    """
    Rewriten tornado.web.RequestHandler methods.

    """
    __timer_start = None
    __timer_last = None
    __request_id = None

    def prepare(self):
        try:
            if self.request.method in ['POST', 'PUT'] and self.request.headers.get('Content-Type', '').startswith('application/json'):
                arguments = self.request.arguments if self.request.arguments else {}
                for key, value in json.loads(self.request.body).iteritems():
                    arguments.setdefault(key, []).append(value)
                self.request.arguments = arguments

            self.__request_id = self.db.execute_lastrowid('INSERT INTO requestlog SET date = NOW(), port = %s, method = %s, url = %s, arguments = %s, user_id = %s, ip = %s, browser = %s;',
                self.settings['port'],
                self.request.method,
                self.request.full_url(),
                str(self.request.arguments)[:1000] if self.request.arguments else None,
                self.get_current_user().id if self.get_current_user() else None,
                self.request.remote_ip,
                self.request.headers.get('User-Agent', None)
            )
        except Exception, e:
            logging.error('Reguest prepare error: ' % e)


    def on_finish(self):
        request_time = self.request.request_time()

        if request_time > (float(self.settings['slow_request_ms'])/1000.0):
            self.settings['slow_request_count'] += 1
            self.settings['slow_request_time'] += request_time
        else:
            self.settings['request_count'] += 1
            self.settings['request_time'] += request_time

        if self.__request_id:
            self.db.execute('UPDATE requestlog SET time = %s, status = %s WHERE id = %s;',
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
        if self.get_argument('user', default=None) and self.get_argument('policy', default=None) and self.get_argument('signature', default=None):
            logging.debug('User/signature auth')
            return self.get_user_by_signature()
        else:
            logging.debug('Session auth')
            return self.get_user_by_session_key(self.get_secure_cookie('session'))

    def get_user_locale(self):
        """
        Sets and returns logged in user locale.

        """
        if self.current_user:
            return locale.get(self.current_user['language'])
        else:
            return locale.get(self.app_settings('language', 'english'))

    def render(self, template_name, **kwargs):
        """
        Includes app title, logo etc to template and renders it.

        """
        kwargs['app_title'] = 'Entu'
        kwargs['app_organisation'] = self.app_settings('name', '')
        kwargs['app_logo'] = 'https://www.entu.ee/public/file-%s' % self.app_settings('photo') if self.app_settings('photo') else '/static/favicon/apple-touch-icon-144-precomposed.png'
        kwargs['page_title'] = '%s - %s' % (kwargs['app_title'], kwargs['page_title']) if kwargs.get('page_title') else '%s - %s' % (kwargs['app_title'], self.app_settings('name', ''))
        kwargs['google_analytics_code'] = self.app_settings('analytics-code')
        kwargs['google_auth_client_id'] = ('%s\n\n' % self.app_settings('auth-google', '', True)).split('\n')[0]
        kwargs['google_auth_api_id'] = ('%s\n\n' % self.app_settings('auth-google', '', True)).split('\n')[2]


        web.RequestHandler.render(self, template_name, **kwargs)

    def json(self, dictionary, status_code=None, allow_origin='*'):
        if status_code:
            self.set_status(status_code)
        if allow_origin:
            self.add_header('Access-Control-Allow-Origin', allow_origin)
        self.add_header('Content-Type', 'application/json')
        self.write(json.dumps(dictionary, cls=JSONDateFix))

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

    def mail_send(self, to, subject='', message=''):
        """
        Sends email using GMail account.

        """

        if type(to) is not list:
            to = StrToList(to)

        if self.current_user:
            from_email = '%s <%s>' % (self.current_user.get('name', ''), self.current_user.get('email', ''))
        else:
            from_email = 'no-reply@entu.ee'

        logging.debug(self.app_settings('auth-mailgun', '\n').split('\n')[0])
        logging.debug(self.app_settings('auth-mailgun', '\n').split('\n')[1])

        http_client = httpclient.HTTPClient()
        response = http_client.fetch('https://api.mailgun.net/v2/%s/messages' % self.app_settings('auth-mailgun', '\n').split('\n')[0],
            method = 'POST',
            auth_username = 'api',
            auth_password = self.app_settings('auth-mailgun', '\n').split('\n')[1],
            body = urllib.urlencode({
                'from'    : from_email.encode('utf-8'),
                'to'      : to,
                'subject' : subject.encode('utf-8').strip(),
                'text'    : message.encode('utf-8').strip()
            }, True)
        )
        return json.loads(response.body)


class JSONDateFix(json.JSONEncoder):
    """
    Formats json.dumps() datetime values to YYYY-MM-DD HH:MM:SS. Use it like json.dumps(mydata, cls=JSONDateFix)

    """
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return time.strftime('%Y-%m-%d %H:%M:%S', obj.timetuple())
        if not isinstance(obj, (basestring, bool)):
            return '%s' % obj
        return json.JSONEncoder.default(self, obj)


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
