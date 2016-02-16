# -*- coding: utf-8 -*-

from pymongo import MongoClient
from raven.contrib.tornado import SentryMixin
from SimpleAES import SimpleAES
from tornado import httpclient
from tornado import locale
from tornado import web

import datetime
import dateutil.parser
import hashlib
import hmac
import json
import logging
import random
import re
import string
import time
import torndb
import urllib


from main.db import *

class myE(Entity):
    __x = None


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
            self.redirect('http://www.entu.ee')
            return

        return self.__app_settings.get(host, {})

    def mongodb(self, database=None):
        """
        Returns MongoDB connection.
        """
        if not database:
            database = self.app_settings('database-name')

        if database == 'www':
            database = 'entu'

        try:
            x = self.settings['mongodbs'][database].server_info()
        except Exception:
            self.settings['mongodbs'][database] = MongoClient(self.settings['mongodb'], serverSelectionTimeoutMS=1000, socketKeepAlive=True)[database]
        return self.settings['mongodbs'][database]

class myUser(myE):
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

        try:
            session = self.mongodb('entu').session.find_one({'key': session_key})
        except IndexError:
            logging.debug('No session!')
            return None
        except Exception, e:
            self.captureException()
            logging.error(e)
            return None

        if not session:
            logging.debug('No session!')
            return None

        if session.get('user', {}).get('email'):
            user_id = session.get('user', {}).get('email')
        else:
            user_id = '%s-%s' % (session.get('user', {}).get('provider'), session.get('user', {}).get('id'))

        user = {
            'user_id': str(session.get('id')),
            'name': session.get('user', {}).get('name'),
            'language': 'estonian',
            'hide_menu': 0,
            'email': session.get('user', {}).get('email'),
            'provider': session.get('user', {}).get('provider'),
            'created_at': session.get('user', {}).get('created'),
            'access_token': None,
            'session_key': session.get('key'),
            'api_key': None
        }
        if session.get('user', {}).get('picture'):
            user['picture'] = session.get('user', {}).get('picture')

        person = self.db.get("""
            SELECT
                property.entity_id,
                (
                    SELECT property.value_string
                    FROM
                        property,
                        property_definition
                    WHERE property_definition.keyname = property.property_definition_keyname
                    AND property.entity_id = entity.id
                    AND property.is_deleted = 0
                    AND property_definition.dataproperty = 'email'
                    ORDER BY property.id
                    LIMIT 1
                ) AS email
            FROM
                entity,
                property,
                property_definition
            WHERE property.entity_id = entity.id
            AND property_definition.keyname = property.property_definition_keyname
            AND property.entity_id = entity.id
            AND entity.is_deleted = 0
            AND property.is_deleted = 0
            AND property_definition.dataproperty = 'entu-user'
            AND property.value_string = %s
            LIMIT 1
        """, user_id)

        if person:
            user['id'] = person.entity_id
            if person.email:
                user['email'] = person.email
        else:
            if self.app_settings('user-parent'):
                if not self.db.get('SELECT entity.id FROM entity, property WHERE property.entity_id = entity.id AND entity.is_deleted = 0 AND property.is_deleted = 0 AND property.property_definition_keyname = "person-entu-user" and property.value_string = %s LIMIT 1', user_id):
                    new_person_id = self.create_entity(entity_definition_keyname='person', parent_entity_id=self.app_settings('user-parent'), ignore_user=True)
                    self.set_property(entity_id=new_person_id, property_definition_keyname='person-entu-user', value=user_id, ignore_user=True)
                    if user['email']:
                        self.set_property(entity_id=new_person_id, property_definition_keyname='person-email', value=user['email'], ignore_user=True)
                    if user['name']:
                        self.set_property(entity_id=new_person_id, property_definition_keyname='person-forename', value=' '.join(user['name'].split(' ')[:-1]), ignore_user=True)
                        self.set_property(entity_id=new_person_id, property_definition_keyname='person-surname', value=user['name'].split(' ')[-1], ignore_user=True)
                    self.set_rights(entity_id=new_person_id, related_entity_id=new_person_id, right='editor', ignore_user=True)

                    user['id'] = new_person_id
                    logging.debug('Created person #%s' % new_person_id)
            else:
                logging.debug('Cant create person - user-parent not configured!')
                return

        if user.get('id'):
            self.__user = user
            self.__session_key = session_key

            logging.debug('Loaded user #%s' % user.get('id'))
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
                (
                    SELECT value_string
                    FROM
                        property,
                        property_definition
                    WHERE property_definition.keyname = property.property_definition_keyname
                    AND property.entity_id = entity.id
                    AND property.is_deleted = 0
                    AND property_definition.dataproperty = 'email'
                    ORDER BY property.id
                    LIMIT 1
                ) AS email,
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

        logging.debug('Loaded user #%s' % user.get('id'))
        return user


class myRequestHandler(SentryMixin, web.RequestHandler, myDatabase, myUser):
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
                    arguments.setdefault(key, []).append('%s' % value)
                self.request.arguments = arguments
        except Exception, e:
            self.captureException()
            logging.error('Reguest arguments error: %s' % e)

        try:
            r = {}
            r['date'] = datetime.datetime.utcnow()
            if self.request.method:
                r['method'] = self.request.method
            if self.request.host:
                r['host'] = self.request.host
            if self.request.path:
                r['path'] = self.request.path
            if self.request.arguments:
                for argument, value in self.request.arguments.iteritems():
                    a = argument.replace('.', '_')
                    r.setdefault('arguments', {})[a] = value
                    if len(r.get('arguments', {}).get(a, [])) < 2:
                        r['arguments'][a] = r['arguments'][a][0]
            if self.get_current_user():
                if self.get_current_user().get('id'):
                    r['user'] = self.get_current_user().get('id')
            if self.request.remote_ip:
                r['ip'] = self.request.remote_ip
            if self.request.headers:
                if self.request.headers.get('User-Agent', None):
                    r['browser'] = self.request.headers.get('User-Agent')

            self.__request_id = self.mongodb('entu').request.insert_one(r).inserted_id
        except Exception, e:
            self.captureException()
            logging.error('Reguest logging error: %s' % e)

    def on_finish(self):
        request_time = self.request.request_time()

        if request_time > (float(self.settings['slow_request_ms'])/1000.0):
            self.settings['slow_request_count'] += 1
            self.settings['slow_request_time'] += request_time
        else:
            self.settings['request_count'] += 1
            self.settings['request_time'] += request_time

        if self.__request_id:
            r = {}
            r['ms'] = int(round(request_time * 1000))
            if self.get_status():
                r['status'] = self.get_status()
            self.mongodb('entu').request.update({'_id': self.__request_id}, {'$set': r}, upsert=False)

    def timer(self, msg=''):
        logging.debug('TIMER: %0.3f - %s' % (round(self.request.request_time(), 3), msg))


    def get_current_user(self):
        """
        Sets and returns logged in user. Properties are, id (Entity ID!), name, language, email, picture. If picture is not set returns gravatar.com picture url.

        """
        if self.get_argument('user', default=None) and self.get_argument('policy', default=None) and self.get_argument('signature', default=None):
            logging.debug('Signature auth')
            return self.get_user_by_signature()
        elif self.request.headers.get('X-Auth-UserId', None) and self.request.headers.get('X-Auth-Token', None):
            logging.debug('Header auth')
            return self.get_user_by_session_key(self.request.headers.get('X-Auth-Token'))
        else:
            logging.debug('Cookie auth')
            return self.get_user_by_session_key(self.get_cookie('session'))

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
        kwargs['app_organisation_id'] = self.app_settings('database-name', '')
        kwargs['app_organisation'] = self.app_settings('name', '')
        kwargs['app_exit_url'] = '%s/exit?next=%s://%s' % (self.settings['auth_url'], self.request.protocol, self.request.host)
        kwargs['intercom_key'] = self.settings['intercom_key']
        kwargs['motd'] = self.app_settings('motd', '')
        kwargs['feedback'] = self.app_settings('feedback-email', '')
        kwargs['homepage'] = self.app_settings('homepage', '')
        kwargs['tagcloud'] = self.app_settings('tagcloud', '')
        kwargs['app_logo'] = 'https://entu.entu.ee/api2/file-%s' % self.app_settings('photo') if self.app_settings('photo') else '/static/favicon/apple-touch-icon-144-precomposed.png'
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

    def head(self, abc=None, **kwargs):
        self.set_status(200)

    def options(self, abc=None, **kwargs):
        self.add_header('Access-Control-Allow-Origin', '*')
        self.add_header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, X-Auth-UserId, X-Auth-Token');
        self.add_header('Access-Control-Allow-Methods', 'GET, PUT, POST, DELETE');

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

    def mail_send(self, to, subject='', message='', html=False, campaign=None, tag=None):
        """
        Sends email using GMail account.

        """

        data = {
            'subject' : subject.encode('utf-8').strip()
        }

        if type(to) is list:
            data['to'] = to
        else:
            data['to'] = StrToList(to)

        if html:
            data['html'] = message.encode('utf-8').strip()
        else:
            data['text'] = message.encode('utf-8').strip()

        if campaign:
            data['o:campaign'] = campaign

        if tag:
            if type(tag) is list:
                data['o:tag'] = tag
            else:
                data['o:tag'] = tag.split(',')
        data.setdefault('o:tag', []).append(self.request.host)

        if self.current_user:
            name = self.current_user.get('name') if self.current_user.get('name') else ''
            email = self.current_user.get('email') if self.current_user.get('email') else 'no-reply@entu.ee'
            data['from'] = u'%s <%s>' % (name, email)
        else:
            data['from'] = 'no-reply@entu.ee'

        http_client = httpclient.HTTPClient()
        response = http_client.fetch('https://api.mailgun.net/v2/%s/messages' % self.app_settings('auth-mailgun', '\n').split('\n')[0],
            method = 'POST',
            auth_username = 'api',
            auth_password = self.app_settings('auth-mailgun', '\n').split('\n')[1],
            body = urllib.urlencode(data, True)
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
