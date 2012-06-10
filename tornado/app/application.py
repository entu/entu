import random
import string
import hashlib
import time
import logging

import db
from helper import *


class ShowSignin(myRequestHandler):
    def get(self):
        """
        Shows application signup/signin page.

        """
        if self.current_user:
            self.clear_cookie('session')
            return self.redirect('/application')

        self.render('application/signin.html',
            page_title = self.get_user_locale().translate('application'),
            message = '',
        )

    def post(self):
        """
        Creates applicant and sends login information to email.

        """
        email = self.get_argument('email', '')
        if not checkEmail(email):
            self.render('application/signin.html',
                page_title = self.get_user_locale().translate('application'),
                message = 'email_error',
            )
            return

        applicant_definition = 10
        applicant_user_definition = 113
        applicant_password_definition = 501

        entity = db.Entity(user_locale=self.get_user_locale())
        entity_id = entity.create(entity_definition_id=applicant_definition)

        entity.set_relations(entity_id=entity_id, user_id=entity_id, relation='owner')

        password = ''.join(random.choice(string.ascii_letters) for x in range(2))
        password += str(entity_id)
        password += ''.join(random.choice(string.ascii_letters) for x in range(3))
        password = password.replace('O', random.choice(string.ascii_lowercase))

        entity.set_property(entity_id=entity_id, property_definition_id=applicant_user_definition, value=email)
        entity.set_property(entity_id=entity_id, property_definition_id=applicant_password_definition, value=password)

        self.mail_send(
            to = email,
            subject = self.get_user_locale().translate('application_signup_email_subject'),
            message = self.get_user_locale().translate('application_signup_email_message') % password
        )

        self.render('application/signin.html',
            page_title = self.get_user_locale().translate('application'),
            message = 'email_success',
        )


class ShowApplication(myRequestHandler):
    def get(self):
        user = self.current_user
        if not user:
            return self.redirect('/application')

        entity = db.Entity(user_locale=self.get_user_locale(), user_id=user.id)
        applicant = entity.get(entity_id=user.id, limit=1)

        self.render('application/form.html',
            page_title = self.get_user_locale().translate('application'),
            applicant = applicant,
        )


    def post(self):
        password = self.get_argument('password', '')

        try:
            entity_id = int(password[2:-3])
            entity = db.Entity(user_locale=self.get_user_locale(), user_id=entity_id)
            applicant = entity.get(entity_id=entity_id, limit=1)
            applicant_id = applicant.get('id')
            applicant_email = applicant.get('properties', {}).get('user', {}).get('values', [])[0].get('value')
            applicant_password = applicant.get('properties', {}).get('password', {}).get('values', [])[0].get('value')
            if applicant_password != password:
                raise Exception('Invalid password')
        except:
            return self.render('application/signin.html',
                page_title = self.get_user_locale().translate('application'),
                message = 'password_error',
            )

        session_key = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(32)) + hashlib.md5(str(time.time())).hexdigest()
        user_key = hashlib.md5(self.request.remote_ip + self.request.headers.get('User-Agent', None)).hexdigest()
        db.User().create(
            provider    = 'application',
            id          = applicant_id,
            email       = applicant_email,
            language    = self.settings['default_language'],
            session     = session_key+user_key
        )
        self.set_secure_cookie('session', str(session_key))

        self.redirect('/application/form')


handlers = [
    ('/application', ShowSignin),
    ('/application/form', ShowApplication),
]
