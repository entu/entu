from tornado import auth
from tornado import web
from tornado import httpclient

from suds.client import Client

import re
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
                google = '%s/google?next=%s' % (self.settings['auth_url'], redirect_url),
                facebook = '%s/facebook?next=%s' % (self.settings['auth_url'], redirect_url),
                live = '%s/live?next=%s' % (self.settings['auth_url'], redirect_url),
                taat = '%s/taat?next=%s' % (self.settings['auth_url'], redirect_url)
            )


class AuthMobileID(myRequestHandler):
    """
    Estonian Mobile ID authentication.

    """
    def post(self):
        service = self.app_settings('auth-mobileid')
        url = 'https://digidocservice.sk.ee/?wsdl'

        client = Client(url)

        mobile = re.sub(r'[^0-9:]', '', self.get_argument('mobile', '', True))
        if mobile:
            if mobile[:3] != '372':
                mobile = '+372%s' % mobile

            person = self.db_get("""
                SELECT
                    p1.value_string AS idcode,
                    p2.value_string AS phone
                FROM
                    property AS p1,
                    property AS p2
                WHERE p1.entity_id = p2.entity_id
                AND p1.property_definition_keyname = 'person-idcode'
                AND p2.property_definition_keyname = 'person-phone'
                AND p1.is_deleted = 0
                AND p2.is_deleted = 0
                AND p2.value_string = %s
                LIMIT 1;
            """, mobile)

            if not person:
                return

            text = self.request.host
            rnd = ''.join(random.choice(string.digits) for x in range(20))

            try:
                mid = client.service.MobileAuthenticate('', '', mobile, 'EST', service, text, rnd, 'asynchClientServer', 0, False, False)
                file_id = self.db_execute_lastrowid('INSERT INTO tmp_file SET filename = %s, file = %s, created = NOW();',
                    'mobileid-%s' % mid.Sesscode,
                    json.dumps({
                        'id': mid.UserIDCode,
                        'name': '%s %s' % (mid.UserGivenname, mid.UserSurname)
                    })
                )
                self.write({
                    'code': mid.ChallengeID,
                    'status': mid.Status,
                    'session': mid.Sesscode,
                    'file': file_id,
                })
            except:
                return

        session = self.get_argument('session', None, True)
        file_id = self.get_argument('file', None, True)
        if session and file_id:
            status = client.service.GetMobileAuthenticateStatus(session, False).Status
            if status == 'OUTSTANDING_TRANSACTION':
                return self.write({'in_progress': True})

            if status != 'USER_AUTHENTICATED':
                return self.write({'status': status})

            user_file = self.db_get('SELECT file FROM tmp_file WHERE id = %s LIMIT 1;', int(file_id))
            if user_file:
                if user_file.get('file'):
                    user = json.loads(user_file.get('file'))
                    session_key = self.user_login(
                        provider        = 'mobileid',
                        provider_id     = user['id'],
                        email           = '%s@eesti.ee' % user['id'],
                        name            = user['name'],
                        picture         = None,
                        redirect_url    = get_redirect(self),
                    )

            return self.write({'url': get_redirect(self)})


handlers = [
    ('/auth', ShowAuthPage),
    ('/auth/mobileid', AuthMobileID),
]
