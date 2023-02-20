from tornado import auth
from tornado import web
from tornado import httpclient

import random
import string
import urllib
import urlparse
import logging
import json

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
    def get(self, provider):
        set_redirect(self)

        self.oauth2_provider = {
            'provider':     'oauth',
            'id':           self.settings['auth_id'],
            'secret':       self.settings['auth_secret'],
            'auth_url':     'https://oauth.ee/auth?client_id=%(id)s&redirect_uri=%(redirect)s&scope=%(scope)s&state=%(state)s&response_type=code',
            'token_url':    'https://oauth.ee/token',
            'info_url':     'https://oauth.ee/user?access_token=%(token)s',
            'scope':        'openid',
            'user_id':      '%(id)s',
            'user_email':   '%(email)s',
            'user_name':    '%(name)s'
        }

        self._OAUTH_AUTHORIZE_URL = self.oauth2_provider['auth_url']

        url = self.request.protocol + '://' + self.request.host + '/auth/' + self.oauth2_provider['provider']

        if not self.get_argument('code', None):
            return self.redirect(self.oauth2_provider['auth_url'] % {
                'id':       self.oauth2_provider['id'],
                'redirect': url,
                'scope':    self.oauth2_provider['scope'],
                'state':    ''.join(random.choice(string.ascii_letters + string.digits) for x in range(16)),
            })

        if self.get_argument('error', None):
            logging.error('%s oauth error: %s' % (provider, self.get_argument('error', None)))
            return self.redirect(get_redirect(self))

        httpclient.AsyncHTTPClient().fetch(self.oauth2_provider['token_url'],
            method = 'POST',
            headers = {'Content-Type': 'application/x-www-form-urlencoded'},
            body = urllib.urlencode({
                'client_id':        self.oauth2_provider['id'],
                'client_secret':    self.oauth2_provider['secret'],
                'redirect_uri':     url,
                'code':             self.get_argument('code', None),
                'grant_type':       'authorization_code',
            }),
            callback = self._got_token,
        )

    @web.asynchronous
    def _got_token(self, response):
        access_token = response.body
        try:
            access_token = json.loads(access_token)
            if 'error' in access_token:
                logging.error('%s oauth error: %s' % (self.oauth2_provider['provider'], access_token['error']))
                return self.redirect(get_redirect(self))
            access_token = access_token['access_token']
        except:
            try:
                access_token = urlparse.parse_qs(access_token)
                if 'error' in access_token:
                    logging.error('%s oauth error: %s' % (self.oauth2_provider['provider'], access_token['error']))
                    return self.redirect(get_redirect(self))
                access_token = access_token['access_token'][0]
            except:
                logging.error('%s oauth error' % self.oauth2_provider['provider'])
                return self.redirect(get_redirect(self))

        httpclient.AsyncHTTPClient().fetch(self.oauth2_provider['info_url'] %  {'token': access_token },
            callback = self._got_user
        )

    @web.asynchronous
    def _got_user(self, response):
        try:
            user = json.loads(response.body)
            access_token = response.effective_url.split('access_token=')[1]
            if 'error' in user:
                logging.error('%s oauth error: %s' % (self.oauth2_provider['provider'], user['error']))
                return self.redirect(get_redirect(self))
        except:
            return

        session_dict = self.user_login(
            provider        = self.oauth2_provider['provider'],
            provider_id     = user.get('id'),
            email           = user.get('email'),
            name            = user.get('name'),
            access_token    = access_token,
            redirect_url    = get_redirect(self),
        )

        self.redirect('https://%(host)s/auth/redirect?key=%(redirect_key)s&user=%(id)s' % session_dict)


class AuthRedirect(myRequestHandler):
    """
    Redirect.

    """
    def get(self):
        self.user_login_redirect(profile_id=self.get_argument('user', None, True), redirect_key=self.get_argument('key', None, True))


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
    ('/auth/redirect', AuthRedirect),
    ('/auth/(.*)', AuthOAuth2),
    ('/exit', Exit),
]
