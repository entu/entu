# -*- coding: utf-8 -*-

from pymongo import MongoClient
from tornado import httpclient
from tornado import locale
from tornado import web

import datetime
import dateutil.parser
import hashlib
import hmac
import json
import logging
import mysql.connector
import random
import re
import string
import time
import urllib


from main.db import *

class myE(Entity):
    __x = None



class myDatabase():
    _app_settings = None


    def db(self, host):
        """
        Returns DB connection.

        """
        try:
            x = self.settings['databases'][host].ping(reconnect=False, attempts=1, delay=0)
        except Exception, err:
            settings = self.get_app_settings(host)
            if settings.get('database-ssl-ca'):
                self.settings['databases'][host] = mysql.connector.connect(
                    host       = settings.get('database-host'),
                    port       = int(settings.get('database-port')),
                    database   = settings.get('database-name'),
                    user       = settings.get('database-user'),
                    password   = settings.get('database-password'),
                    use_pure   = False,
                    autocommit = True,
                    ssl_ca     = settings.get('database-ssl-ca'),
                    ssl_verify_cert = True
                )
            else:
                self.settings['databases'][host] = mysql.connector.connect(
                    host       = settings.get('database-host'),
                    port       = int(settings.get('database-port')),
                    database   = settings.get('database-name'),
                    user       = settings.get('database-user'),
                    password   = settings.get('database-password'),
                    use_pure   = False,
                    autocommit = True
                )
            logging.error('MySQL - ' + settings.get('database-name'))


        return self.settings['databases'][host]


    def db_get(self, sql=None, *args, **kwargs):
        if not sql:
            return

        cursor = self.db(self.request.host).cursor(dictionary=True, buffered=True)
        try:
            cursor.execute('SET SESSION MAX_EXECUTION_TIME=30000;')
        except Exception, err:
            pass

        try:
            if args:
                cursor.execute(sql, tuple(args))
            elif kwargs:
                cursor.execute(sql, kwargs)
            else:
                cursor.execute(sql)
        except Exception, err:
            logging.error('%s\n%s\n%s\n%s\n%s' % (err, sql, args, kwargs, cursor.statement))

        result = cursor.fetchone()

        if not result:
            return None

        new_row = {}
        for key, value in result.iteritems():
            if isinstance(value, (bytes, bytearray)):
                new_row[key] = value.decode('utf-8')
            else:
                new_row[key] = value

        cursor.close()

        return new_row


    def db_query(self, sql=None, *args, **kwargs):
        if not sql:
            return

        cursor = self.db(self.request.host).cursor(dictionary=True, buffered=True)
        try:
            cursor.execute('SET SESSION MAX_EXECUTION_TIME=30000;')
        except Exception, err:
            pass

        try:
            if args:
                cursor.execute(sql, tuple(args))
            elif kwargs:
                cursor.execute(sql, kwargs)
            else:
                cursor.execute(sql)
        except Exception, err:
            logging.error('%s\n%s\n%s\n%s\n%s' % (err, sql, args, kwargs, cursor.statement))

        result = []
        for row in cursor:
            new_row = {}
            for key, value in row.iteritems():
                if isinstance(value, (bytes, bytearray)):
                    new_row[key] = value.decode('utf-8')
                else:
                    new_row[key] = value
            result.append(new_row)
        cursor.close()

        return result


    def db_execute(self, sql=None, *args, **kwargs):
        if not sql:
            return

        db = self.db(self.request.host)
        cursor = db.cursor(buffered=True)

        try:
            if args:
                cursor.execute(sql, tuple(args))
            elif kwargs:
                cursor.execute(sql, kwargs)
            else:
                cursor.execute(sql)
        except Exception, err:
            logging.error('%s\n%s\n%s\n%s\n%s' % (err, sql, args, kwargs, cursor.statement))

        db.commit()
        cursor.close()

        return True


    def db_execute_lastrowid(self, sql=None, *args, **kwargs):
        if not sql:
            return

        db = self.db(self.request.host)
        cursor = db.cursor(buffered=True)

        try:
            if args:
                cursor.execute(sql, tuple(args))
            elif kwargs:
                cursor.execute(sql, kwargs)
            else:
                cursor.execute(sql)
        except Exception, err:
            logging.error('%s\n%s\n%s\n%s\n%s' % (err, sql, args, kwargs, cursor.statement))

        result = cursor.lastrowid

        db.commit()
        cursor.close()

        return result


    def app_settings(self, key, default=None, do_something_fun=False):
        if self.get_app_settings():
            return self.get_app_settings().get(key, default)


    def get_app_settings(self, host=None):
        if not host:
            host = self.request.host

        if host == 'entu.ee':
            self.redirect('https://www.entu.ee')
            return

        if not self._app_settings:
            logging.debug('Loaded app_settings for %s.' % host)

            if self.settings.get('database-ssl-ca'):
                db = mysql.connector.connect(
                    host       = self.settings['database-host'],
                    port       = int(self.settings['database-port']),
                    database   = self.settings['database-database'],
                    user       = self.settings['database-user'],
                    password   = self.settings['database-password'],
                    use_pure   = False,
                    autocommit = True,
                    ssl_ca     = self.settings['database-ssl-ca'],
                    ssl_verify_cert = True
                )
            else:
                db = mysql.connector.connect(
                    host       = self.settings['database-host'],
                    port       = int(self.settings['database-port']),
                    database   = self.settings['database-database'],
                    user       = self.settings['database-user'],
                    password   = self.settings['database-password'],
                    use_pure   = False,
                    autocommit = True
                )

            cursor = db.cursor(dictionary=True, buffered=True)

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
                                property_definition.datatype='boolean',
                                property.value_boolean,
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

            cursor.execute(sql)

            customers = {}
            for c in cursor:
                customers.setdefault(c['entity'], {})[c['property'].decode('utf-8')] = c['value']

            cursor.close()
            db.close()

            self._app_settings = {}
            for c in customers.values():
                self._app_settings[c.get('domain', '')] = c

        if not self._app_settings.get(host):
            try:
                self.send_error(404)
            except Exception, e:
                pass
            return

        return self._app_settings.get(host, {})


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
        except Exception, e:
            self.settings['mongodbs'][database] = MongoClient(self.settings['mongodb'], connect=True)
            logging.error('Mongo - ' + database)
        return self.settings['mongodbs'][database][database]



class myUser(myE):
    __user        = None
    __session_key = None
    __user_id     = None
    __policy      = None
    __signature   = None


    def user_login(self, email=None, redirect_url=None, remote_ip=None, browser=None):
        """
        Starts session. Creates new (or updates old) user.

        """
        session_key = str(''.join(random.choice(string.ascii_letters + string.digits) for x in range(32)) + hashlib.md5(str(time.time())).hexdigest())

        logging.warning(email)
        logging.warning(session_key)
        logging.warning(redirect_url)
        logging.warning(remote_ip)
        logging.warning(browser)

        self.db_execute('INSERT INTO session SET key = %s, email = %s, ip = %s, browser = %s, created = NOW();',
            # insert
            session_key,
            email,
            remote_ip,
            browser
        )

        return {'session_key': session_key, 'redirect_url': redirect_url}


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

        if self.request.remote_ip:
            user['ip'] = self.request.remote_ip

        person = self.db_get("""
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
            user['id'] = person.get('entity_id')

            if person.get('email'):
                user['email'] = person.get('email')

            person_name = self.db_get("""
                SELECT
                    (SELECT value_string FROM property WHERE entity_id = %s AND is_deleted = 0 AND property_definition_keyname = 'person-forename' LIMIT 1) AS forename,
                    (SELECT value_string FROM property WHERE entity_id = %s
                     AND is_deleted = 0 AND property_definition_keyname = 'person-surname' LIMIT 1) AS surname
            """, user['id'], user['id'])

            if person_name.get('forename') or person_name.get('surname'):
                user['name'] = (person_name.get('forename') if person_name.get('forename') else '') + (' ' + person_name.get('surname') if person_name.get('surname') else '')

        else:
            if self.app_settings('user-parent'):
                if not self.db_get('SELECT entity.id FROM entity, property WHERE property.entity_id = entity.id AND entity.is_deleted = 0 AND property.is_deleted = 0 AND property.property_definition_keyname = \'person-entu-user\' and property.value_string = %s LIMIT 1', user_id):
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

                    self.redirect('/entity/person/%s' % new_person_id)
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

        user = self.db_get("""
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

        if not user.get('api_key'):
            logging.debug('No user API key!')
            return

        correct_signature = hmac.new(user.get('api_key', '').encode('utf-8'), policy.encode('utf-8'), hashlib.sha1).digest().encode('base64').replace('\n','')
        if signature != correct_signature:
            logging.debug('Wrong signature!')
            return

        self.__user = user
        self.__user_id = user_id
        self.__policy = policy
        self.__signature = signature

        logging.debug('Loaded user #%s' % user.get('id'))
        return user



class myRequestHandler(web.RequestHandler, myDatabase, myUser):
    """
    Rewriten tornado.web.RequestHandler methods.

    """
    def prepare(self):
        if self.request.protocol.upper() == 'HTTP':
            logging.error(self.request.host + self.request.uri)
            self.redirect('https://' + self.request.host + self.request.uri)
            return

        try:
            if self.request.method in ['POST', 'PUT'] and self.request.headers.get('Content-Type', '').startswith('application/json'):
                arguments = self.request.arguments if self.request.arguments else {}
                for key, value in json.loads(self.request.body).iteritems():
                    arguments.setdefault(key, []).append('%s' % value)
                self.request.arguments = arguments
        except Exception, e:
            logging.error('Reguest arguments error: %s' % e)

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
        kwargs['motd'] = self.app_settings('motd', '')
        kwargs['feedback'] = self.app_settings('feedback-email', '')
        kwargs['homepage'] = self.app_settings('homepage', '')
        kwargs['tagcloud'] = self.app_settings('tagcloud', '')
        kwargs['app_logo'] = 'https://entu.entu.ee/api2/file-%s' % self.app_settings('photo') if self.app_settings('photo') else '/static/images/favicons/apple-touch-icon-144-precomposed.png'
        kwargs['page_title'] = '%s - %s' % (kwargs['app_title'], kwargs['page_title']) if kwargs.get('page_title') else '%s - %s' % (kwargs['app_title'], self.app_settings('name', ''))

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
        try:
            self.set_status(404)
            self.render('main/template/404.html',
                page_title = '404'
            )
        except Exception:
            pass

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
        response = http_client.fetch('https://api.eu.mailgun.net/v2/%s/messages' % self.app_settings('auth-mailgun', '\n').split('\n')[0],
            method = 'POST',
            auth_username = 'api',
            auth_password = self.app_settings('auth-mailgun', '\n').split('\n')[1],
            body = urllib.urlencode(data, True)
        )
        logging.error(response.body)
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
