import logging

import db
from helper import *


class ShowSignin(myRequestHandler):
    def get(self):
        """
        Shows application signup/signin page.

        """
        self.clear_cookie('session')
        self.render('application/signin.html',
            page_title = self.get_user_locale().translate('application'),
        )

    def post(self):
        """
        Creates applicant and sends login information to email.

        """
        email = self.get_attribute('email', None)
        if not email:
            self.redirect('/application')




handlers = [
    ('/application', ShowSignin),
]
