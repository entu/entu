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
            ('/person/set_role', SetRole),
        ])


if __name__ == '__main__':
    main()