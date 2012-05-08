from tornado import auth, web

from helper import *


class MainHandler(myRequestHandler):
    @web.authenticated
    def get(self):
        self.write(self.current_user)


handlers = [
    (r'/', MainHandler),
]
