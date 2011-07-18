from bo import *
from database.person import *
from django.template import TemplateDoesNotExist


class ShowPerson(boRequestHandler):
    def get(self, id):
        if self.authorize('bubbler'):

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

            try:
                self.view(person.displayname, 'person/person_' + Person().current.current_role.template_name + '.html', {
                    'person': person,
                    'roles': roles,
                    'changed': changeinfo,
                })
            except TemplateDoesNotExist:
                self.view(person.displayname, 'person/person.html', {
                    'person': person,
                    'roles': roles,
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
                    if field in ['forename', 'surname']:
                        setattr(person, field, value)
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


def main():
    Route([
            ('/person/set_role', SetRole),
            (r'/person/(.*)', ShowPerson),
        ])


if __name__ == '__main__':
    main()