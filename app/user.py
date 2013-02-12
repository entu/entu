from tornado import auth, web

import db
from helper import *


class ShowUserPreferences(myRequestHandler):
    @web.removeslash
    @web.authenticated
    def get(self):
        """
        Show user preferences.

        """
        self.render('user/preferences.html')

    @web.removeslash
    @web.authenticated
    def post(self):
        """
        Save user preferences

        """
        if self.get_argument('language', None, True) in ['estonian', 'english']:
            self.current_user['language'] = self.get_argument('language', None, True)


handlers = [
    ('/user/preferences', ShowUserPreferences),
]
