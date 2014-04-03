import socket

from main.helper import *
from main.db import *


class ShowInfoPage(myRequestHandler, Entity):
    def get(self, language='et'):

        language = language.strip(' .')
        if language not in ['et']:
            language = 'et'

        self.render('info/template/%s.html' % language,
            language = language
        )


class RegisterNewCusomer(myRequestHandler, Entity):
    def post(self):
        company = self.get_argument('company', default='company', strip=True)
        domain = self.get_argument('domain', default='', strip=True)
        name = self.get_argument('name', default='name', strip=True)
        email = self.get_argument('email', default='', strip=True)
        ip = self.request.remote_ip
        try:
            host = socket.gethostbyaddr(self.request.remote_ip)[0]
        except Exception, e:
            host = ''
        remote_addr = '%s\n%s' % (ip, host) if host else ip

        self.mail_send(
            to = 'info@entu.ee',
            subject = 'Registreerumine',
            message = 'Asutus:\n%s\n\nDomeen:\n%s\n\nNimi:\n%s\n\nE-post:\n%s\n\nIP:\n%s' % (company, domain, name, email, remote_addr)
        )

        # customer_id = self.create_entity(entity_definition_keyname='customer')
        # self.set_property(entity_id=customer_id, property_definition_keyname='name', value=name)
        # self.set_property(entity_id=customer_id, property_definition_keyname='domain', value=domain)

        # person_id = self.create_entity(entity_definition_keyname='person', parent_entity_id=customer_id)
        # self.set_property(entity_id=person_id, property_definition_keyname='surname', value=name.split(' ')[0])
        # self.set_property(entity_id=person_id, property_definition_keyname='forename', value=' '.join(name.split(' ')[1:]).strip())
        # self.set_property(entity_id=person_id, property_definition_keyname='email', value=email)

        self.write('OK')


handlers = [
    ('/info/register', RegisterNewCusomer),
    (r'/info(.*)', ShowInfoPage),
]
