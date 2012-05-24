from tornado import auth
from tornado import web
from tornado import httpclient

import random
import string
import hashlib
import time
import urllib
import urlparse
import logging
import json

from helper import *
from db import *


class AuthOAuth2(myRequestHandler, auth.OAuth2Mixin):
    @web.asynchronous
    def get(self, provider):
        # self.require_setting('google_client_key', 'Google OAuth2')
        # self.require_setting('google_client_secret', 'Google OAuth2')

        self.oauth2_provider = None

        if provider == 'facebook' and 'facebook_api_key' in self.settings and 'facebook_secret' in self.settings:
            # https://developers.facebook.com/apps
            self.oauth2_provider = {
                'provider':     'facebook',
                'key':          self.settings['facebook_api_key'],
                'secret':       self.settings['facebook_secret'],
                'auth_url':     'https://www.facebook.com/dialog/oauth?client_id=%(id)s&redirect_uri=%(redirect)s&scope=%(scope)s&state=%(state)s',
                'token_url':    'https://graph.facebook.com/oauth/access_token',
                'info_url':     'https://graph.facebook.com/me?access_token=%(token)s',
                'scope':        'email',
                'user_id':      '%(id)s',
                'user_email':   '%(email)s',
                'user_name':    '%(name)s',
                'user_picture': 'http://graph.facebook.com/%(id)s/picture?type=large',
            }

        if provider == 'google' and 'google_client_key' in self.settings and 'google_client_secret' in self.settings:
            # https://code.google.com/apis/console
            self.oauth2_provider = {
                'provider':     'google',
                'key':          self.settings['google_client_key'],
                'secret':       self.settings['google_client_secret'],
                'auth_url':     'https://accounts.google.com/o/oauth2/auth?client_id=%(id)s&redirect_uri=%(redirect)s&scope=%(scope)s&state=%(state)s&response_type=code&approval_prompt=auto&access_type=online',
                'token_url':    'https://accounts.google.com/o/oauth2/token',
                'info_url':     'https://www.googleapis.com/oauth2/v2/userinfo?access_token=%(token)s',
                'scope':        'https://www.googleapis.com/auth/userinfo.profile+https://www.googleapis.com/auth/userinfo.email',
                'user_id':      '%(id)s',
                'user_email':   '%(email)s',
                'user_name':    '%(name)s',
                'user_picture': '%(picture)s',
            }
        if provider == 'live' and 'live_client_key' in self.settings and 'live_client_secret' in self.settings:
            # https://manage.dev.live.com/Applications/Index
            self.oauth2_provider = {
                'provider':     'live',
                'key':          self.settings['live_client_key'],
                'secret':       self.settings['live_client_secret'],
                'auth_url':     'https://oauth.live.com/authorize?client_id=%(id)s&redirect_uri=%(redirect)s&scope=%(scope)s&state=%(state)s&response_type=code',
                'token_url':    'https://oauth.live.com/token',
                'info_url':     'https://apis.live.net/v5.0/me?access_token=%(token)s',
                'scope':        'wl.signin+wl.emails',
                'user_id':      '%(id)s',
                'user_email':   '',
                'user_name':    '%(name)s',
                'user_picture': 'https://apis.live.net/v5.0/%(id)s/picture',
            }

        if not self.oauth2_provider:
            return self.finish()

        self._OAUTH_AUTHORIZE_URL = self.oauth2_provider['auth_url']

        url = self.request.protocol + '://' + self.request.host + '/auth/' + provider

        if not self.get_argument('code', None):
            return self.redirect(self.oauth2_provider['auth_url'] % {
                'id':       self.oauth2_provider['key'],
                'redirect': url,
                'scope':    self.oauth2_provider['scope'],
                'state':    ''.join(random.choice(string.ascii_letters + string.digits) for x in range(16)),
            })

        if self.get_argument('error', None):
            logging.error('%s oauth error: %s' % (provider, self.get_argument('error', None)))
            return self.redirect('/')

        httpclient.AsyncHTTPClient().fetch(self.oauth2_provider['token_url'],
            method = 'POST',
            headers = {'Content-Type': 'application/x-www-form-urlencoded'},
            body = urllib.urlencode({
                'client_id':        self.oauth2_provider['key'],
                'client_secret':    self.oauth2_provider['secret'],
                'redirect_uri':     url,
                'code':             self.get_argument('code', None),
                'grant_type':       'authorization_code',
            }),
            callback = self._got_token,
        )

    @web.asynchronous
    def _got_token(self, response):
        # self.write(response.body)
        # self.finish()
        access_token = response.body
        try:
            access_token = json.loads(access_token)
            if 'error' in access_token:
                logging.error('%s oauth error: %s' % (provider, access_token['error']))
                return self.redirect('/')
            access_token = access_token['access_token']
        except:
            access_token = urlparse.parse_qs(access_token)
            if 'error' in access_token:
                logging.error('%s oauth error: %s' % (provider, access_token['error']))
                return self.redirect('/')
            access_token = access_token['access_token'][0]

        httpclient.AsyncHTTPClient().fetch(self.oauth2_provider['info_url'] %  {'token': access_token },
            callback = self._got_user
        )

    @web.asynchronous
    def _got_user(self, response):
        # self.write(response.body)
        # self.finish()
        try:
            user = json.loads(response.body)
            if 'error' in user:
                logging.error('%s oauth error: %s' % (provider, user['error']))
                return self.redirect('/')
        except:
            return

        if self.oauth2_provider['provider'] == 'facebook':
            LoginUser(self, {
                'provider': self.oauth2_provider['provider'],
                'id':       user.setdefault('id', None),
                'email':    user.setdefault('email', None),
                'name':     user.setdefault('name', None),
                'picture':  'http://graph.facebook.com/%s/picture?type=large' % user.setdefault('id', ''),
            })
        if self.oauth2_provider['provider'] == 'google':
            LoginUser(self, {
                'provider': self.oauth2_provider['provider'],
                'id':       user.setdefault('id', None),
                'email':    user.setdefault('email', None),
                'name':     user.setdefault('name', None),
                'picture':  user.setdefault('picture', None),
            })
        if self.oauth2_provider['provider'] == 'live':
            LoginUser(self, {
                'provider': self.oauth2_provider['provider'],
                'id':       user.setdefault('id', None),
                'email':    user.setdefault('emails', {}).setdefault('preferred', user.setdefault('emails', {}).setdefault('preferred', user.setdefault('personal', {}).setdefault('account', None))),
                'name':     user.setdefault('name', None),
                'picture':  'https://apis.live.net/v5.0/%s/picture' % user.setdefault('id', ''),
            })

        self.finish()


class AuthMobileID(myRequestHandler, auth.OpenIdMixin):
    @web.asynchronous
    def get(self):
        self._OPENID_ENDPOINT = 'https://openid.ee/server/xrds/mid'

        if not self.get_argument('openid.mode', None):
            url = self.request.protocol + '://' + self.request.host + '/auth/mobileid'
            self.authenticate_redirect(callback_uri=url)

        self.get_authenticated_user(self.async_callback(self._got_user))

    def _got_user(self, user):
        if not user:
            raise web.HTTPError(500, 'MobileID auth failed')

        LoginUser(self, {'id': self.get_argument('openid.identity', None)})
        self.finish()


class AuthIDcard(myRequestHandler, auth.OpenIdMixin):
    @web.asynchronous
    def get(self):
        self._OPENID_ENDPOINT = 'https://openid.ee/server/eid'

        if not self.get_argument('openid.mode', None):
            return self.authenticate_redirect()

        self.get_authenticated_user(self.async_callback(self._got_user))

    def _got_user(self, user):
        if not user:
            raise web.HTTPError(500, 'IDcard auth failed')

        LoginUser(self, {'id': self.get_argument('openid.identity', None)})
        self.finish()


class AuthTwitter(myRequestHandler, auth.TwitterMixin):
    @web.asynchronous
    def get(self):
        if not self.get_argument('oauth_token', None):
            return self.authenticate_redirect()
        self.get_authenticated_user(self.async_callback(self._got_user))

    def _got_user(self, user):
        if not user:
            raise web.HTTPError(500, 'Twitter auth failed')

        LoginUser(self, {
            'provider': 'twitter',
            'id':       '%s' % user.setdefault('id'),
            'email':    None,
            'name':     user.setdefault('name'),
            'picture':  user.setdefault('profile_image_url'),
        })
        self.finish()


def LoginUser(rh, user):
    # return rh.write(user)

    session_key = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(32)) + hashlib.md5(str(time.time())).hexdigest()
    user_key = hashlib.md5(rh.request.remote_ip + rh.request.headers.get('User-Agent', None)).hexdigest()

    profile_id = myDb().db.execute_lastrowid('INSERT INTO user_profile SET provider = %s, provider_id = %s, email = %s, name = %s, picture = %s, session = %s, created = NOW() ON DUPLICATE KEY UPDATE email = %s, name = %s, picture = %s, session = %s, changed = NOW();',
            user['provider'],
            user['id'],
            user['email'],
            user['name'],
            user['picture'],
            session_key+user_key,
            user['email'],
            user['name'],
            user['picture'],
            session_key+user_key
        )
    profile = myDb().db.get('SELECT id, user_id FROM user_profile WHERE id = %s', profile_id)

    if not profile.user_id:
        user_id = myDb().db.execute_lastrowid('INSERT INTO user SET email = %s, name = %s, picture = %s, language = %s, created = NOW();',
            user['email'],
            user['name'],
            user['picture'],
            rh.settings['default_language']
        )
        myDb().db.execute('UPDATE user_profile SET user_id = %s WHERE id = %s;', user_id, profile.id)

    rh.set_secure_cookie('session', str(session_key))
    rh.redirect('/')


class Exit(myRequestHandler):
    def get(self):
        self.clear_cookie('session')
        self.redirect('/public')


handlers = [
    ('/auth/mobileid', AuthMobileID),
    ('/auth/idcard', AuthIDcard),
    ('/auth/twitter', AuthTwitter),
    ('/auth/(.*)', AuthOAuth2),
    ('/exit', Exit),
]
