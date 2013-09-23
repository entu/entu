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


handlers = [
    (r'/info(.*)', ShowInfoPage),
]
