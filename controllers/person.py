from bo import *
from database.person import *


class SetRole(boRequestHandler):
    def post(self):

        role_key = self.request.get('role').strip()
        if role_key:
            p = Person().current
            p.current_role = db.Key(role_key)
            p.put()


def main():
    Route([
            ('/person', ShowPersonFilter),
            ('/person/list', ShowPersonList),
            ('/person/set_role', SetRole),
            (r'/person(.*)', ShowPerson),
        ])


if __name__ == '__main__':
    main()