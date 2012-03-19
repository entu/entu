from operator import attrgetter

from bo import *
from database.zimport.zoin import *
from database.person import *
from database.bubble import *
from database.feedback import *


class ShowPersonList(boRequestHandler):
    def get(self):
        if not self.authorize('bubbler'):
            return

        self.view(
            main_template = 'main/index.html',
            template_file = 'main/list.html',
            page_title = 'page_persons',
            values = {
                'list_url': '/person',
                'content_url': '/person/show',
                'toolbar': [{'url': '/person/merge', 'title': Translate('person_duplicates'), 'icon': 'join'}]
            }
        )

    def post(self):
        if not self.authorize('bubbler'):
            return

        key = self.request.get('key').strip()
        if key:
            person = Person().get(key)
            person.AutoFix()
            self.echo_json({
                'id': person.key().id(),
                'key': str(person.key()),
                'image': person.GetPhotoUrl(32),
                'title': person.displayname,
                'info': ', '.join(person.users) if person.users else '',
                'email': person.primary_email if person.primary_email else '',
                'idcode': person.idcode if person.idcode else '',
                'birth_date': person.birth_date.strftime('%d.%m.%Y') if person.birth_date else '',
            })
            return

        keys = None
        search = self.request.get('search').strip().lower()
        bubble_seeders = self.request.get('bubble_seeders').strip()
        bubble_leechers = self.request.get('bubble_leechers').strip()
        bubble_waitinglist = self.request.get('bubble_waitinglist').strip()
        person_duplicates = self.request.get('person_duplicates').strip()

        if search:
            keys = [str(k) for k in list(db.Query(Person, keys_only=True).filter('_is_deleted', False).filter('search', search).order('sort'))]

        if bubble_seeders:
            bubble = Bubble().get(bubble_seeders)
            keys = [str(k) for k in bubble.seeders]

        if bubble_leechers:
            bubble = Bubble().get(bubble_leechers)
            leechers = Person().get(bubble.leechers)
            keys = [str(k.key()) for k in sorted(leechers, key=attrgetter('sort'))]

        if bubble_waitinglist:
            bubblepersons = [] # db.Query(BubblePerson).filter('_is_deleted', False).filter('bubble', db.Key(bubble_waitinglist)).filter('status', 'waiting').order('start_datetime')
            keys = [str(k.person.key()) for k in bubblepersons]

        if person_duplicates:
            person = Person().get(person_duplicates)
            same_user = []
            same_idcode = []
            same_name = []

            for user in person.users:
                same_user = ListMerge(same_user, [str(k) for k in list(db.Query(Person, keys_only=True).filter('_is_deleted', False).filter('users', user))])
            same_idcode = [] if not person.idcode else [str(k) for k in list(db.Query(Person, keys_only=True).filter('_is_deleted', False).filter('idcode', person.idcode))]
            same_name = [] if not person.displayname else [str(p.key()) for p in list(db.Query(Person).filter('_is_deleted', False).filter('search', person.displayname.lower()))]
            keys = sorted(ListUnique(same_user + same_idcode + same_name))


        if keys == None:
            keys = [str(k) for k in list(db.Query(Person, keys_only=True).filter('_is_deleted', False).order('sort'))]

        self.echo_json({'keys': keys})


class ShowPerson(boRequestHandler):
    def get(self, person_id):
        if not self.authorize('bubbler'):
            return

        person = Person().get_by_id(int(person_id))
        person.photourl = person.GetPhotoUrl(150)
        self.view(
            main_template = 'main/index.html',
            template_file = 'person/info.html',
            values = {
                'person': person,
            }
        )


class ExportPersonsCSV(boRequestHandler):
    def get(self):
        if not self.authorize('bubbler'):
            return

        bubble_leechers = self.request.get('bubble_leechers').strip()
        if bubble_leechers:
            bubble = Bubble().get(bubble_leechers)
            filename = bubble.GetType().displayname + ' - ' + bubble.displayname + ' - ' + Translate('bubble_leechers').lower()
            rowslist = []
            for p in Person().get(bubble.leechers):
                email = p.primary_email
                if not email:
                    email = ''
                rowslist.append([
                    p.displayname.encode("utf-8"),
                    email.encode("utf-8"),
                ])

        self.echo_csv(
            filename = filename,
            rowslist = rowslist
        )


class MergeDuplicates(boRequestHandler):
    def get(self, page = ''):
        if not self.authorize('bubbler'):
            return

        page = int(page.strip('/')) if page.strip('/') else 1
        limit = 300
        offset = limit * (page-1)
        persons = [str(k) for k in list(db.Query(Person, keys_only=True).filter('_is_deleted', False).order('sort').fetch(limit=limit, offset=offset))]

        self.view(
            main_template = 'main/index.html',
            template_file = 'person/merge.html',
            page_title = 'person_duplicates',
            values = {
                'persons': persons,
                'next_page': page + 1,
            }
        )

    def post(self, page = None):
        if not self.authorize('bubbler'):
            return

        ids = StrToList(self.request.get('person_ids'))
        keys = [str(db.Key.from_path('Person', int(i))) for i in ids]

        target_p = Person()
        for person_key in keys:
            source_p = Person().get(person_key)
            source_pk = source_p.key()

            target_p.users                  = ListMerge(target_p.users,source_p.users)
            target_p.email                 = source_p.email if not target_p.email else target_p.email
            target_p.password              = source_p.password if not target_p.password else target_p.password
            target_p.forename              = source_p.forename if not target_p.forename else target_p.forename
            target_p.surname               = source_p.surname if not target_p.surname else target_p.surname
            target_p.idcode                = source_p.idcode if not target_p.idcode else target_p.idcode
            target_p.citizenship           = source_p.citizenship if not target_p.citizenship else target_p.citizenship
            target_p.country_of_residence  = source_p.country_of_residence if not target_p.country_of_residence else target_p.country_of_residence
            target_p.gender                = source_p.gender if not target_p.gender else target_p.gender
            target_p.birth_date            = source_p.birth_date if not target_p.birth_date else target_p.birth_date
            target_p.roles                 = ListMerge(target_p.roles, source_p.roles)
            target_p.leecher               = ListMerge(target_p.leecher + source_p.leecher)
            target_p.seeder                = ListMerge(target_p.seeder + source_p.seeder)
            target_p.merged_from           = ListMerge(source_pk, target_p.merged_from)
            target_p.put()

            source_p._is_deleted = True
            source_p.put()

        target_p.AutoFix()
        target_pk = target_p.key()

        taskqueue.Task(url='/taskqueue/person_merge', params={'source_ids': self.request.get('person_ids'), 'target_key': str(target_p.key())}).add(queue_name='one-by-one')

        self.echo_json({'keys': keys})












class ExportAllPersonsZoinCSV(boRequestHandler):
    def get(self):
        if not self.authorize('bubbler'):
            return

        rowslist = []
        for z in db.Query(Zoin).filter('entity_kind', 'Person'):
            rowslist.append([
                z.key().id_or_name(),
                z.new_key
            ])

        self.echo_csv(
            filename = 'zoin_person',
            rowslist = rowslist
        )




class ExportAllPersonsCSV(boRequestHandler):
    def get(self,pagesize,pagenum):
        if not self.authorize('bubbler'):
            return

        rowslist = []
        for p in db.Query(Person).fetch(int(pagesize),int(pagesize)*int(pagenum)):
            if p.user:
                if not re.search('@',p.user):
                    p.user = ''
            if p.apps_username:
                if not re.search('@',p.apps_username):
                    p.apps_username = ''
#                    p.put()
            if not p.forename:
                p.forename = ''
            if not p.surname:
                p.surname = ''

            rowslist.append([
                p.key(),
                p.key().id_or_name(),
                p.forename.encode("utf-8"),
                p.surname.encode("utf-8"),
                p.apps_username,
                p.birth_date,
                p.idcode,
                p.user,
            ])

        self.echo_csv(
            filename = 'persons '+ str(int(pagesize)*int(pagenum)) + '-' + str(int(pagesize)*int(pagenum)+int(pagesize)),
            rowslist = rowslist
        )




class ShowPerson1(boRequestHandler):
    def get(self, id):

        current_person = Person().current_s(self)
        if not current_person:
            self.redirect('/person/signin')
            return

        if id == '':
            id = current_person.key().id()

        can_search = True

        try:
            authorized = self.authorize('reception')
        except AttributeError: # AttributeError: 'NoneType' object has no attribute 'roles2'
            authorized = False

        if ( not authorized ):
            id = current_person.key().id()
            can_search = False

        if id == current_person.key().id():
            person = current_person
        else:
            person = Person().get_by_id(int(id))

        if not person:
            self.view('N/A', 'person/notfound.html', )
            return

        roles = db.Query(Role).fetch(1000)

        for r in roles:
            if r.key() in person.roles:
                r.is_selected = True

        changeinfo = ''
        last_change = person.last_change
        if last_change:
            if last_change.user:
                changer = db.Query(Person).filter('user', last_change.user).get()
                if changer:
                    changeinfo = Translate('person_changed_on') % {'name': changer.displayname, 'date': UtcToLocalDateTime(last_change.datetime).strftime('%d.%m.%Y %H:%M')}

        grades = db.Query(Grade).filter('person',person.key()).fetch(1000)
        grades = sorted(grades, key=lambda k: k.datetime)

        ratings = ListRatings()
        ratings.head = [
            Translate('bubble_displayname').encode("utf-8"),
            Translate('grade_name').encode("utf-8"),
            Translate('grade_equivalent').encode("utf-8"),
            Translate('date').encode("utf-8"),
        ]
        ratings.data = []
        for grade in grades:
            rating = ListedRating()
            rating.name = grade.bubble.displayname.encode("utf-8")
            rating.grade = grade.displayname.encode("utf-8")
            rating.equivalent = grade.equivalent
            rating.date = grade.displaydate.encode("utf-8")
            ratings.data.append(rating)

        try:
            self.view(person.displayname, 'person/person_' + current_person.current_role.template_name + '.html', {
                'can_search': can_search,
                'person': person,
                'roles': roles,
                'ratings': ratings,
                'changed': changeinfo,
            })
        except (TemplateDoesNotExist, AttributeError):
            self.view(person.displayname, 'person/person.html', {
                'can_search': can_search,
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
                            person.roles = ListMerge(db.Key(role_key), person.roles)
                        else:
                            person.roles = ListSubtract(person.roles, db.Key(role_key))

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
        if ( not self.authorize('reception') and person.key() != person.current.key() ):
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
# Should probably be part of BO and named differently, too
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
            (r'/person/show/(.*)', ShowPerson),
            (r'/person/merge(.*)', MergeDuplicates),
            ('/person/csv', ExportPersonsCSV),
            ('/person/zoin', ExportAllPersonsZoinCSV),
            ('/person/all_csv/(.*)/(.*)', ExportAllPersonsCSV),
            ('/person/set_role', SetRole),
            ('/person/person_ids', GetPersonIds),
            ('/person/person_keys', GetPersonKeys),
            (r'/person/grades_csv/(.*)', GradesCSV),
            ('/person', ShowPersonList),
        ])


if __name__ == '__main__':
    main()
