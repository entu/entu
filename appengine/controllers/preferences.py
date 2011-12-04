from pytz.gae import pytz

from bo import *
from database.person import *


class ShowPreferences(boRequestHandler):
    def get(self):
        self.view(
            page_title = 'page_preferences',
            template_file = 'preferences.html',
            values = {
                'person': Person().current,
                'preferences': UserPreferences().current,
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
