from datetime import datetime

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
        # if self.current_user:
        #     self.clear_cookie('session')
        #     return self.redirect('/application')

        self.render('application/error.html',
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

        entity.set_relations(entity_id=entity_id, related_entity_id=entity_id, relationship_type='viewer')

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
        applicant = entity.get(entity_id=user.id, limit=1, full_definition=True)

        submissions = {}
        for s in entity.get(entity_definition_id=20, only_public=True):
            start_datetime = s.get('properties', {}).get('start_datetime', {}).get('values', [])
            if not start_datetime:
                continue
            start_datetime = start_datetime[0]
            if not start_datetime['db_value']:
                continue
            if start_datetime['db_value'] > datetime.now():
                continue

            end_datetime = s.get('properties', {}).get('end_datetime', {}).get('values', [])
            if not end_datetime:
                continue
            end_datetime = end_datetime[0]
            if not end_datetime['db_value']:
                continue
            if end_datetime['db_value'] < datetime.now():
                continue


            parent1 = entity.get_relatives(related_entity_id=s.get('id'), relation_type='child', reverse_relation=True, only_public=True).values()
            if not parent1:
                continue
            parent1 = parent1[0][0]
            parent2 = entity.get_relatives(related_entity_id=parent1.get('id'), relation_type='child', reverse_relation=True, only_public=True).values()
            if not parent2:
                continue
            parent2 = parent2[0][0]

            submissions.setdefault(parent2.get('displayname'), {})['label'] = parent2.get('displayname')
            submissions.setdefault(parent2.get('displayname'), {}).setdefault('childs', []).append({
                'id': s.get('id'),
                'label': s.get('displayname'),
                'info': s.get('displayinfo'),
                'url': ''.join([x['value'] for x in s.get('properties', {}).get('url', {}).get('values', []) if x['value']]),
                'subscribed': True if entity.get_relatives(entity_id=s.get('id'), related_entity_id=user.id, relation_type='leecher', reverse_relation=True) else False
            })

        properties = {}
        for k, p in applicant.get('properties', {}).iteritems():
            if not p.get('fieldset'):
                continue
            properties.setdefault(p.get('fieldset'), {})['label'] = p.get('fieldset')
            properties.setdefault(p.get('fieldset'), {}).setdefault('properties', {})[k] = p

        childs = []
        for ed in entity.get_entity_definition(entity_definition_id=[5, 19, 21, 25, 50, 51, 12]):
            relatives = entity.get_relatives(entity_id=user.id, entity_definition_id=ed.id, relation_type='child', full_definition=True)
            if relatives:
                relatives = relatives.values()[0]
            else:
                relatives = [entity.get(entity_id=0, entity_definition_id=ed.id, limit=1, full_definition=True)]

            childs.append({
                'label': ed.label,
                'description': ed.description if ed.description else '',
                'childs': relatives,
                'ordinal': ed.ordinal
            })


        self.render('application/form.html',
            page_title = self.get_user_locale().translate('application'),
            properties = properties,
            submissions = submissions,
            childs = childs,
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


class SaveApplication(myRequestHandler):
    def post(self):
        """
        Saves applicant info.

        """
        user = self.current_user
        if not user:
            return

        entity = db.Entity(user_locale=self.get_user_locale(), user_id=user.id)
        applicant = entity.get(entity_id=user.id, limit=1)
        if not applicant:
            return

        property_definition_id  = self.get_argument('property_id', default=None, strip=True)
        property_id             = self.get_argument('value_id', default=None, strip=True)
        value                   = self.get_argument('value', default=None, strip=True)
        uploaded_file           = self.request.files.get('file', [])[0] if self.request.files.get('file', None) else None

        property_id = entity.set_property(entity_id=user.id, property_definition_id=property_definition_id, value=value, property_id=property_id, uploaded_file=uploaded_file)

        self.write({
            'property_id': property_definition_id,
            'value_id': property_id,
            'value': uploaded_file['filename'] if uploaded_file else value
        })


class SaveApplicationChild(myRequestHandler):
    def post(self):
        """
        Saves applicant info.

        """
        user = self.current_user
        if not user:
            logging.debug('no user')
            return

        entity = db.Entity(user_locale=self.get_user_locale(), user_id=user.id)
        applicant = entity.get(entity_id=user.id, limit=1)
        if not applicant:
            logging.debug('no applicant')
            return

        entity_id               = self.get_argument('entity_id', default=None, strip=True)
        entity_definition_id    = self.get_argument('entity_definition_id', default=None, strip=True)
        property_definition_id  = self.get_argument('property_id', default=None, strip=True)
        property_id             = self.get_argument('value_id', default=None, strip=True)
        value                   = self.get_argument('value', default=None, strip=True)
        uploaded_file           = self.request.files.get('file', [])[0] if self.request.files.get('file', None) else None

        if not entity_definition_id:
            logging.debug('no entity_definition_id')
            return

        if not entity_id:
            entity_id = entity.create(entity_definition_id=entity_definition_id, parent_entity_id=user.id)

        property_id = entity.set_property(entity_id=entity_id, property_definition_id=property_definition_id, value=value, property_id=property_id, uploaded_file=uploaded_file)

        self.write({
            'entity_id': entity_id,
            'property_id': property_definition_id,
            'value_id': property_id,
            'value': uploaded_file['filename'] if uploaded_file else value
        })


class Subscribe(myRequestHandler):
    def post(self):
        """
        Saves applicant info.

        """
        user = self.current_user
        if not user:
            return

        action = self.get_argument('action', '')
        entity_id = self.get_argument('entity_id', '')
        if not action or not entity_id:
            return

        entity = db.Entity(user_locale=self.get_user_locale(), user_id=user.id)
        applicant = entity.get(entity_id=user.id, limit=1, full_definition=True)
        if not applicant:
            return

        logging.debug(action)

        if action.lower() == 'subscribe':
            entity.set_relations(entity_id=entity_id, related_entity_id=user.id, relationship_type='leecher')
        if action.lower() == 'unsubscribe':
            entity.set_relations(entity_id=entity_id, related_entity_id=user.id, relationship_type='leecher', delete=True)


handlers = [
    ('/application', ShowSignin),
    # ('/application/form', ShowApplication),
    # ('/application/save', SaveApplication),
    # ('/application/save/child', SaveApplicationChild),
    # ('/application/subscribe', Subscribe),
]
