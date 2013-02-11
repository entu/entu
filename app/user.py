from tornado import auth, web

import db
from helper import *


class ShowUserPreferences(myRequestHandler):
    @web.removeslash
    @web.authenticated
    def get(self, entity_definition_keyname=None):
        """
        Show user preferences.

        """
        self.render('user/preferences.html',
        )


handlers = [
    ('/user/preferences', ShowUserPreferences),
]
