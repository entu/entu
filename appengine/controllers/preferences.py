from pytz.gae import pytz

from bo import *
from database.person import *


class ShowPreferences(boRequestHandler):
    def get(self):
        languages = []
        for l in SystemPreferences().get('languages'):
            languages.append({'value': l, 'label': self.translate('language_%s' % l)})
        self.view(
            main_template='main/index.html',
            template_file = 'preferences.html',
            page_title = 'page_preferences',
            values = {
                'person': Person().current,
                'preferences': UserPreferences().current,
                'languages': languages,
                'timezones': pytz.common_timezones,
            }
        )

    def post(self):
        field = self.request.get('field').strip()
        value = self.request.get('value').strip()

        UserPreferences().set(field, value)


def main():
    Route([
             ('/preferences', ShowPreferences),
            ])


if __name__ == '__main__':
    main()
