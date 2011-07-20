from bo import *
from database.person import *
from database.bubble import *
from django.template import TemplateDoesNotExist

import csv
import cStringIO


class ShowPerson(boRequestHandler):
    def get(self, id):

        if id == '':
            self.view('??', 'person/person.html', {
            })
            return

        person = Person().get_by_id(int(id))
        if not person:
            self.view('N/A', 'person/notfound.html', {
                'person_id': id,
            })
            return

        roles = db.Query(Role).fetch(1000)

        for r in roles:
            if r.key() in person.roles:
                r.is_selected = True

        changeinfo = ''
        last_change = person.last_change
        if last_change:
            if last_change.user:
                changer = db.Query(Person).filter('apps_username', last_change.user).get()
                if changer:
                    changeinfo = Translate('person_changed_on') % {'name': changer.displayname, 'date': UtcToLocalDateTime(last_change.datetime).strftime('%d.%m.%Y %H:%M')}

        ratings = ListRatings()
        ratings.head = [
            Translate('bubble_displayname').encode("utf-8"),
            Translate('grade_name').encode("utf-8"),
            Translate('grade_equivalent').encode("utf-8"),
            Translate('date').encode("utf-8"),
        ]

        grades = db.Query(Grade).filter('person',person.key()).fetch(1000)
        grades = sorted(grades, key=lambda k: k.datetime)
        
        for grade in grades:
            rating = ListedRating()
            rating.name = grade.bubble.displayname.encode("utf-8")
            rating.grade = grade.displayname.encode("utf-8")
            rating.equivalent = grade.equivalent
            rating.date = grade.displaydate.encode("utf-8")
            ratings.data.append(rating)

        try:
            self.view(person.displayname, 'person/person_' + Person().current.current_role.template_name + '.html', {
                'person': person,
                'roles': roles,
                'ratings': ratings,
                'changed': changeinfo,
            })
        except TemplateDoesNotExist:
            self.view(person.displayname, 'person/person.html', {
                'person': person,
                'roles': roles,
                'ratings': ratings,
                'changed': changeinfo,
            })

    def post(self, key):
        if self.authorize('change_person'):
            person = Person().get(key)
            field = self.request.get('field').strip()
            value = self.request.get('value').strip()
            role_key = self.request.get('role').strip()

            if person:
                if value:
                    if field in ['forename', 'surname', 'idcode']:
                        setattr(person, field, value)
                        person.index_names()
                    if field in ['person_birthdate']:
                        setattr(person, field, datetime.strptime(value, '%d.%m.%Y'))
                    if field == 'primary_email':
                        person.email = value
                    if field == 'role' and role_key:
                        if value.lower() == 'true':
                            person.roles = AddToList(db.Key(role_key), person.roles)
                        else:
                            person.roles = RemoveFromList(db.Key(role_key), person.roles)

                person.put()


class SetRole(boRequestHandler):
    def post(self):

        role_key = self.request.get('role').strip()
        if role_key:
            p = Person().current
            p.current_role = db.Key(role_key)
            p.put()


class GetPersonIds(boRequestHandler):
    def get(self):

        query = self.request.get('query').strip()
        keys = []
        data = []
        names = []
        for p in db.Query(Person).filter('search_names', query.lower()).fetch(50):
            data.append(str(p.key().id()))
            names.append(p.displayname)
        respond = {
            'query': query.lower(),
            'suggestions': names,
            'data': data,
        }

        self.echo_json(respond)


class GetPersonKeys(boRequestHandler):
    def get(self):

        query = self.request.get('query').strip()
        keys = []
        data = []
        names = []
        for p in db.Query(Person).filter('search_names', query.lower()).fetch(50):
            data.append(str(p.key()))
            names.append(p.displayname)
        respond = {
            'query': query.lower(),
            'suggestions': names,
            'data': data,
        }

        self.echo_json(respond)
        

#CSV fail hinnetest 

class GradesCSV(boRequestHandler):
    def get(self, person_id):
        person = Person().get_by_id(int(person_id))
        if ( not self.authorize('reception') and person.Key() != Person.current().Key() ):
            return

        csvfile = cStringIO.StringIO()
        csvWriter = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)

        csvWriter.writerow([
            Translate('bubble_displayname').encode("utf-8"),
            Translate('grade_name').encode("utf-8"),
            Translate('grade_equivalent').encode("utf-8"),
            Translate('date').encode("utf-8"),
            ])
        grades = db.Query(Grade).filter('person',person.key()).fetch(1000)
        for grade in sorted(grades, key=lambda k: k.datetime):
            csvWriter.writerow([
                grade.bubble.displayname.encode("utf-8"),
                grade.displayname.encode("utf-8"),
                grade.equivalent,
                grade.displaydate.encode("utf-8"),
            ])
        

        self.header('Content-Type', 'text/csv; charset=utf-8')
        self.header('Content-Disposition', 'attachment; filename=' + unicode(person.displayname.encode("utf-8"), errors='ignore') + '.csv')
        self.echo(csvfile.getvalue())
        csvfile.close()

#Hinnete tabel
       
class ListRatings(boRequestHandler):
    head = []
    data = []


class ListedRating(boRequestHandler):
    name        = ''
    grade       = ''
    equivalent  = 0
    date        = ''


def main():
    Route([
            ('/person/set_role', SetRole),
            ('/person/person_ids', GetPersonIds),
            ('/person/person_keys', GetPersonKeys),
            (r'/person/grades_csv/(.*)', GradesCSV),
            ('/person', ShowPerson),
            (r'/person/(.*)', ShowPerson),
        ])


if __name__ == '__main__':
    main()