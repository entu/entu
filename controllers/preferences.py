from bo import *
from database import *


class ShowPreferences(boRequestHandler):
    def get(self):
        self.view('preferences', 'preferences.html', {
            'person': Person().current,
            'preferences': UserPreferences().current,
        })

    def post(self):
        UserPreferences().set_language(self.request.get('language'))


def main():
    Route([
             ('/preferences', ShowPreferences),
            ])


if __name__ == '__main__':
    main()