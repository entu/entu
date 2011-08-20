# -*- coding: utf-8 -*-

import gdata.apps.service
import gdata.alt.appengine

import bz2, base64, string, re

from bo import *
from database.person import *

def GenerateUsername(forename, surname):
    username = forename + '.' + surname
    username = username.lower()
    username = username.encode('utf-8')
    letters = {'å':'a', 'ä':'a', 'ö':'o', 'õ':'o', 'ü':'y', 'š':'s', 'ž':'z'}
    for c in letters:
        username = username.replace(c, letters[c])
    username = re.sub('[^a-z/.]', '', username)
    return username
    

class CreateAppsAccount(boRequestHandler):
    def get(self):
        redirect = self.request.get('r').strip()
        persons_ids = self.request.get('p').strip().strip('.').split('.')
        if persons_ids:
            persons_ids = [int(i) for i in persons_ids]

        persons = Person().get_by_id(persons_ids)
        for p in persons:
            if not p.apps_username:
                p.apps_username = GenerateUsername(p.forename, p.surname)

        self.view('', 'googleapps/create_account.html', {
            'persons': persons,
            'redirect': redirect,
        })


    def post(self):
        gapps = gdata.apps.service.AppsService(
            domain = SystemPreferences().get('google_apps_domain'),
            email = SystemPreferences().get('google_apps_user'),
            password = bz2.decompress(base64.b64decode(SystemPreferences().get('google_apps_password'))),
        )
        gdata.alt.appengine.run_on_appengine(gapps)
        gapps.ProgrammaticLogin()

        gapps.CreateUser(
            user_name = 'test.kasutaja2',
            family_name = 'Test',
            given_name = 'Kasutaja2',
            password = '123456789aB',
            change_password = 'true'
        )
        
        #for user in gapps.RetrievePageOfUsers(start_username=None).entry:
        #    self.echo(user.name.given_name + ' ' + user.name.family_name + ' ' + user.login.user_name)


def main():
    Route([
            ('/gapps/createaccount', CreateAppsAccount),
        ])


if __name__ == '__main__':
    main()
