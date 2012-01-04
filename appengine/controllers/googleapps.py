# -*- coding: utf-8 -*-

import gdata.apps.service
import gdata.alt.appengine

import bz2, base64, string, re
import random, string

from bo import *
from database.person import *

def GenerateUsername(forename, surname):
    username = forename + '.' + surname
    username = username.lower()
    username = username.encode('utf-8')
    letters = {'å':'a', 'ä':'a', 'é':'e', 'ö':'o', 'õ':'o', 'ü':'y', 'š':'sh', 'ž':'zh'}
    for c in letters:
        username = username.replace(c, letters[c])
    username = re.sub('[^a-z/.]', '', username)
    return username


class CheckAppsAccount(boRequestHandler):
    def post(self):
        if not self.authorize('gapps_account_create'):
            return

        gapps = gdata.apps.service.AppsService(
            domain = SystemPreferences().get('google_apps_domain'),
            email = SystemPreferences().get('google_apps_user'),
            password = bz2.decompress(base64.b64decode(SystemPreferences().get('google_apps_password'))),
        )
        gdata.alt.appengine.run_on_appengine(gapps)
        gapps.ProgrammaticLogin()

        person_id = self.request.get('person_id').strip()
        person = Person().get_by_id(int(person_id))
        if person.user:
            username = person.user.replace('@'+SystemPreferences().get('google_apps_domain'), '')
        else:
            forename = person.forename if person.forename else ''
            surname = person.surname if person.surname else ''
            username = GenerateUsername(forename, surname)

        user = None
        try:
            user = gapps.RetrieveUser(username)
        except gdata.apps.service.AppsForYourDomainException , e:
            if e.error_code != 1301:
                raise

        nick = None
        try:
            nick = gapps.RetrieveNickname(username)
        except gdata.apps.service.AppsForYourDomainException , e:
            if e.error_code != 1301:
                raise

        result = {}
        if person.user:
            if not user and not nick:
                result['text'] = Translate('gapps_create_account') % username
                result['url'] = '/gapps/createaccount'
        else:
            if user:
                result['text'] = Translate('gapps_user_exist') % username
                result['url'] = '/gapps/connectaccount/%s' % username
            if nick:
                result['text'] = Translate('gapps_nickname_exist') % {'nick': username, 'user': nick.login.user_name}
                result['url'] = '/gapps/connectaccount/%s' % username
            if not user and not nick:
                result['text'] = Translate('gapps_create_account') % username
                result['url'] = '/gapps/createaccount'

        self.echo_json(result)


class CreateAppsAccount(boRequestHandler):
    def post(self):
        if not self.authorize('gapps_account_create'):
            return

        gapps = gdata.apps.service.AppsService(
            domain = SystemPreferences().get('google_apps_domain'),
            email = SystemPreferences().get('google_apps_user'),
            password = bz2.decompress(base64.b64decode(SystemPreferences().get('google_apps_password'))),
        )
        gdata.alt.appengine.run_on_appengine(gapps)
        gapps.ProgrammaticLogin()

        person_id = self.request.get('person_id').strip()
        person = Person().get_by_id(int(person_id))
        if person.user:
            username = person.user.replace('@'+SystemPreferences().get('google_apps_domain'), '')
        else:
            forename = person.forename if person.forename else ''
            surname = person.surname if person.surname else ''
            username = GenerateUsername(forename, surname)

        if not person.password:
            password = ''.join(random.choice(string.ascii_letters) for x in range(3))
            password += str(person.key().id())
            password += ''.join(random.choice(string.ascii_letters) for x in range(3))
            password = password.replace('O', random.choice(string.ascii_lowercase))
            person.password = password
            person.put()

        person.user = username + '@' + SystemPreferences().get('google_apps_domain')
        person.put()

        SendMail(
            to = person.emails,
            subject = Translate('gapps_account_created_subject'),
            message = Translate('gapps_account_created_message') % {'user': username, 'email': person.user, 'password': person.password}
        )

        gapps.CreateUser(
            user_name = username,
            given_name = person.forename,
            family_name = person.surname,
            password = person.password,
            change_password = 'true'
        )

        result = {}

        self.echo_json(result)

        #for user in gapps.RetrievePageOfUsers(start_username=None).entry:
        #    self.echo(user.name.given_name + ' ' + user.name.family_name + ' ' + user.login.user_name)


class ConnectAppsAccount(boRequestHandler):
    def post(self, username):
        if not self.authorize('gapps_account_create'):
            return

        person_id = self.request.get('person_id').strip()
        person = Person().get_by_id(int(person_id))
        person.user = username + '@' + SystemPreferences().get('google_apps_domain')
        person.put()


def main():
    Route([
            ('/gapps/checkaccount', CheckAppsAccount),
            ('/gapps/createaccount', CreateAppsAccount),
            (r'/gapps/connectaccount/(.*)', ConnectAppsAccount),
        ])


if __name__ == '__main__':
    main()
