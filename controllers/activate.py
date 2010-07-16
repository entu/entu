import hashlib
from time import time
from random import random

from google.appengine.api import mail
from google.appengine.api import users
import urllib

from boFunctions import *


class Activate(webapp.RequestHandler):
    def get(self, url):
        self.redirect(users.create_logout_url('/user/activate' + urllib.unquote(url).decode('utf8')))

    def post(self, url):
        email = self.request.POST.get('email')

        if email and mail.is_email_valid(email):
            key = hashlib.md5(str(time() * random()) + email).hexdigest()

            link = 'http://' + self.request.headers.get('host') + '/activate/' + email + '/' + key

            c = db.Query(Contact).filter('value =', email).get()
            if not c:
                p = Person()
                p.save()

                c = Contact()
                c.person = p
                c.type = 'email'
                c.value = email

            c.activation_key = key
            c.save()

            message = mail.EmailMessage()
            message.sender = 'argoroots@gmail.com'
            message.to = email
            message.subject = boTranslate('activation_subject')
            message.html = boTranslate('activation_email') % link
            message.send()

            self.response.out.write(boTranslate('registration_info_sent') % email)

def main():
    boWSGIApp([
             (r'/activate(.*)', Activate),
            ])


if __name__ == '__main__':
    main()