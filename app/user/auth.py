from tornado import auth
from tornado import web
from tornado import httpclient

import random
import string
import logging
import json
import ssl

from main.helper import *


class ShowAuthPage(myRequestHandler):
    """
    Show Log in page.

    """
    def get(self):
        self.clear_all_cookies()
        self.clear_all_cookies(domain=self.settings['cookie_domain'])

        redirect_url = self.get_argument('next', '', strip=True)
        if redirect_url:
            if 'http' not in redirect_url:
                redirect_url = self.request.protocol + '://' + self.request.host + redirect_url

        if self.get_cookie('auth_provider'):
            self.redirect('%s/%s?next=%s' % (self.settings['auth_url'], self.get_cookie('auth_provider'), redirect_url))
        else:
            self.render('user/template/auth.html',
                redirect_url = redirect_url,
                mobileid = '%s/mobile-id' % self.settings['auth_url'],
                idcard = '%s/id-card?next=%s' % (self.settings['auth_url'], redirect_url),
                google = '%s/google?next=%s' % (self.settings['auth_url'], redirect_url),
                taat = '%s/taat?next=%s' % (self.settings['auth_url'], redirect_url)
            )


class Exit(myRequestHandler):
    """
    Log out.

    """
    def get(self):
        redirect_url = '/'
        if self.current_user:
            if self.current_user.provider == 'google':
                redirect_url = 'https://www.google.com/accounts/logout'
            elif self.current_user.provider == 'facebook':
                redirect_url = 'https://www.facebook.com/logout.php?access_token=%s&confirm=1&next=%s://%s/status' % (self.current_user.access_token, self.request.protocol, self.request.host)
            elif self.current_user.provider == 'live':
                redirect_url = 'https://login.live.com/oauth20_logout.srf?client_id=%s&redirect_uri=%s://%s/status' % (self.app_settings('auth-live', '\n', True).split('\n')[0], self.request.protocol, self.request.host)

            self.user_logout()

        self.redirect(redirect_url)


class AuthOAuth2(myRequestHandler, auth.OAuth2Mixin):
    """
    OAuth.ee authentication.

    """
    @web.asynchronous
    def get(self):
        set_redirect(self)

        self.oauth2_provider = {
            'id':           self.settings['auth_id'],
            'secret':       self.settings['auth_secret'],
            'auth_url':     'https://oauth.ee/auth?client_id=%(id)s&redirect_uri=%(redirect)s&scope=openid&state=%(state)s&response_type=code',
            'token_url':    'https://oauth.ee/token',
            'info_url':     'https://oauth.ee/user',
            'scope':        'openid'
        }

        self._OAUTH_AUTHORIZE_URL = self.oauth2_provider['auth_url']

        if not self.get_argument('code', None):
            return self.redirect(self.oauth2_provider['auth_url'] % {
                'id':       self.oauth2_provider['id'],
                'redirect': self.request.protocol + '://' + self.request.host + '/auth/oauth',
                'state':    ''.join(random.choice(string.ascii_letters + string.digits) for x in range(16)),
            })

        if self.get_argument('error', None):
            logging.error('Auth error: %s' % self.get_argument('error', None))
            return self.redirect(get_redirect(self))

        httpclient.AsyncHTTPClient().fetch(self.oauth2_provider['token_url'],
            method = 'POST',
            headers = {'Content-Type': 'application/json'},
            body = json.dumps({
                'client_id':        self.oauth2_provider['id'],
                'client_secret':    self.oauth2_provider['secret'],
                'code':             self.get_argument('code', None),
                'grant_type':       'authorization_code',
            }),
            ssl_options = {'validate_cert': False},
            callback = self._got_token,
        )

    @web.asynchronous
    def _got_token(self, response):
        logging.warning('ssl version: %s' % ssl.OPENSSL_VERSION)
        logging.warning('response: %s' % response)

        try:
            access_token = json.loads(response.body)
            if 'error' in access_token:
                logging.error('Auth error: %s' % access_token['error'])
                return self.redirect(get_redirect(self))
            access_token = access_token['access_token']
        except:
            logging.error('Auth error')
            return self.redirect(get_redirect(self))

        httpclient.AsyncHTTPClient().fetch(self.oauth2_provider['info_url'],
            headers = {'Authorization': 'Bearer %s' % access_token},
            ssl_options = {'validate_cert': False},
            callback = self._got_user
        )

    @web.asynchronous
    def _got_user(self, response):
        logging.warning('response: %s' % response)

        try:
            user = json.loads(response.body)
            if 'error' in user:
                logging.error('Auth error: %s' % user['error'])
                return self.redirect(get_redirect(self))
        except:
            return

        session_dict = self.user_login(
            email        = user.get('email'),
            redirect_url = get_redirect(self),
        )

        self.clear_cookie('session')
        self.set_cookie(name='session', value=session_dict['session_key'], expires_days=14)
        self.redirect(session_dict['redirect_url'])


def set_redirect(rh):
    """
    Saves requested URL to cookie, then (after authentication) we know where to go.

    """
    if rh.get_argument('next', None, strip=True):
        rh.set_secure_cookie('auth_redirect', rh.get_argument('next', default='/', strip=True), 1)


def get_redirect(rh):
    """
    Returns requested URL (or / if not set) from cookie.

    """
    redirect_url = rh.get_secure_cookie('auth_redirect')
    if redirect_url:
        return redirect_url
    return '/'


handlers = [
    ('/auth', ShowAuthPage),
    ('/auth/oauth', AuthOAuth2),
    ('/exit', Exit),
]
