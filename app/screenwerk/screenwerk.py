import logging

from main.helper import *
from main.db import *


class ShowPlayer(myRequestHandler):
    def get(self):
        if self.current_user.email != 'mihkel.putrinsh@gmail.com':
            return

        updateFormulas(entity_id=entity_id, user_locale=self.get_user_locale(), user_id=self.current_user.id)
