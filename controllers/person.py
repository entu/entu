from google.appengine.api import users

from bo import *
from database import *

import urllib


class ShowPersonFilter(boRequestHandler):
    def get(self):

        levels = db.Query(Translation).filter('dictionary_name', 'level_of_education').filter('language', User().current.language).order('value').fetch(1000)

        roles = db.Query(Translation).filter('dictionary_name', 'role_name').filter('language', User().current.language).order('value').fetch(1000)

        departments = []
        for d in db.Query(Translation).filter('dictionary_name', 'department_name').filter('language', User().current.language).order('value').fetch(1000):
            for d1 in d.dictionary.department_names:
                if not d1.parent_department:
                    departments.append(d1)

        self.view('persons', 'person.html', {
            'levels': levels,
            'departments': departments,
            'roles': roles,
        })

class ShowPersonList(boRequestHandler):
    def post(self):
        level = self.request.get('level')
        department = self.request.get('department')
        role = self.request.get('role')


        proles = db.Query(PersonRole)
        if len(department) > 0:
            proles.filter('department', db.Key(department))
        if len(role) > 0:
            proles.filter('role', db.Key(role))
        proles.fetch(1000)

        roles = [r.person.key for r in proles]

        #persons = db.Query(Person).filter('__key__', roles).fetch(1000)

        self.response.out.write(proles)


class ShowPerson(boRequestHandler):
    def get(self, key = None):

        p = db.Query(Person).filter('__key__', db.Key(key.strip('/'))).get()

        self.view(p.forename + ' ' + p.surname, 'person_tree.html', {
            'person': p,
        })


def main():
    Route([
            ('/person', ShowPersonFilter),
            ('/person/list', ShowPersonList),
            (r'/person(.*)', ShowPerson),
        ])


if __name__ == '__main__':
    main()