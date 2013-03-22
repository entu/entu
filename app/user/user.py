from tornado import auth, web

from helper import *


class ShowUserPreferences(myRequestHandler):
    @web.removeslash
    @web.authenticated
    def get(self):
        """
        Show user preferences.

        """
        self.render('user/template/preferences.html')

    @web.removeslash
    @web.authenticated
    def post(self):
        """
        Save user preferences

        """
        self.current_user[self.get_argument('property', None, True)] = self.get_argument('value', None, True)


handlers = [
    ('/user/preferences', ShowUserPreferences),
]
