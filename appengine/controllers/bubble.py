import string
import csv
import cStringIO
from datetime import *

from bo import *
from database.bubble import *
from database.person import *
from database.dictionary import *


class ShowBubbleList(boRequestHandler):
    def get(self, bubbletype):
        if not self.authorize('bubbler'):
            return

        self.view(
            page_title = 'page_bubbles',
            template_file = 'main/list.html',
            values = {
                'list_url': '/bubble/%s' % bubbletype,
                'content_url': '/bubble/show',
            }
        )

    def post(self, bubbletype):
        if not self.authorize('bubbler'):
            return

        key = self.request.get('key').strip()
        search = self.request.get('search').strip()

        if key:
            bubble = Bubble().get(key)
            self.echo_json({
                'id': bubble.key().id(),
                'image': None,
                'title': bubble.displayname,
                'info': bubble.displaydate,
            })

        else:
            if search:
                keys = [str(k) for k in list(db.Query(Bubble, keys_only=True).filter('type', bubbletype).filter('sort_estonian >=', search).filter('is_deleted', False).order('sort_estonian'))]
            else:
                keys = [str(k) for k in list(db.Query(Bubble, keys_only=True).filter('type', bubbletype).filter('is_deleted', False).order('sort_estonian'))]
            self.echo_json({'keys': keys})


class ShowBubble(boRequestHandler):
    def get(self, bubble_id):
        if not self.authorize('bubbler'):
            return

        bubble = Bubble().get_by_id(int(bubble_id))

        self.view(
            template_file = 'bubble/bubble_info.html',
            values = {
                'bubble': bubble,
            }
        )





class ShowBubble1(boRequestHandler):
    def get(self, id):
        if self.authorize('bubbler'):

            bubble = Bubble().get_by_id(int(id))
            bubble_key = bubble.key()

#            nextinline_bubbles = []
#            for mb in bubble.InBubbles:
#                nextinline_bubbles.append(mb)
#                for mb2 in mb.SubBubbles:
#                    if mb2.key() != bubble.key():
#                        nextinline_bubbles.append(mb2)
#                    mb2_subbubbles = mb2.SubBubbles
#                    if mb2_subbubbles:
#                        nextinline_bubbles.extend(mb2_subbubbles)

            nextinline_bubbles_d = {}

            in_bubbles_d = bubble.InBubblesD
            nextinline_bubbles_d.update( in_bubbles_d )

            for in_bubble in in_bubbles_d.values():
                sibling_bubbles_d = in_bubble.SubBubblesD
                nextinline_bubbles_d.update( sibling_bubbles_d )

                for sibling_bubble in sibling_bubbles_d.values():
                    child_bubbles_d = sibling_bubble.SubBubblesD
                    nextinline_bubbles_d.update( child_bubbles_d )

            nextinline_bubbles_d[bubble_key] = 'foo'
            del nextinline_bubbles_d[bubble_key]

            nextinline_bubbles = nextinline_bubbles_d.values()

            ratingscales = db.Query(RatingScale).fetch(1000)

            #addable_bubbles = db.Query(Bubble).filter('__key__ !=', bubble.key()).filter('type IN', bubble.type2.allowed_subtypes).filter('is_deleted', False).fetch(1000)
            addable_bubbles = nextinline_bubbles
            prerequisite_bubbles = nextinline_bubbles

            changeinfo = ''
            last_change = bubble.last_change
            if last_change:
                if last_change.user:
                    changer = db.Query(Person).filter('apps_username', last_change.user).get()
                    if changer:
                        changeinfo = Translate('bubble_changed_on') % {'name': changer.displayname, 'date': UtcToLocalDateTime(last_change.datetime).strftime('%d.%m.%Y %H:%M')}

            self.view(bubble.type2.displayname + ' - ' + bubble.displayname, 'bubble/bubble.html', {
                'bubble': bubble,
                'changed': changeinfo,
                'ratingscales': ratingscales,
                'addable_bubbles': addable_bubbles,
                'nextinline_bubbles': nextinline_bubbles,
                'prerequisite_bubbles': prerequisite_bubbles,
            })

    def post(self, key):
        if self.authorize('bubbler'):
            bubble = Bubble().get(key)
            field = self.request.get('field').strip()
            value = self.request.get('value').strip()
            if bubble:
                if value:
                    if field in ['name', 'description', 'badge']:
                        setattr(bubble, field, DictionaryAdd(('bubble_' + field), value))
                        if field == 'name':
                            bubble.sort_estonian = StringToSortable(value)
                    if field in ['start_datetime', 'end_datetime']:
                        setattr(bubble, field, datetime.strptime(value, '%d.%m.%Y %H:%M'))
                    if field == 'rating_scale':
                        bubble.rating_scale = db.Key(value)
                    if field == 'url':
                        bubble.url = value
                    if field == 'nextinline':
                        bubble.next_in_line = AddToList(db.Key(value), bubble.next_in_line)
                    if field == 'prerequisite':
                        bubble.prerequisite_bubbles = AddToList(db.Key(value), bubble.prerequisite_bubbles)
                    if field == 'is_mandatory':
                        subbubble = self.request.get('subbubble').strip()
                        if subbubble:
                            if value.lower() == 'true':
                                bubble.mandatory_bubbles = AddToList(db.Key(subbubble), bubble.mandatory_bubbles)
                                bubble.optional_bubbles = RemoveFromList(db.Key(subbubble), bubble.optional_bubbles)
                                taskqueue.Task(url='/taskqueue/bubble_copy_leechers', params={'from_bubble_key': str(bubble.key()), 'to_bubble_key': subbubble}).add(queue_name='one-by-one')
                            else:
                                bubble.optional_bubbles = AddToList(db.Key(subbubble), bubble.optional_bubbles)
                                bubble.mandatory_bubbles = RemoveFromList(db.Key(subbubble), bubble.mandatory_bubbles)
                else:
                    setattr(bubble, field, None)

                bubble.put()
                bubble.displayname_cache_reset()


class AddBubble(boRequestHandler):
    def get(self, type, key):
        if self.authorize('bubbler'):
            bubble = Bubble().get(key)
            if bubble:

                new = Bubble()
                new.type = type
                new.name = DictionaryAdd('bubble_name', '')
                new.start_datetime = bubble.start_datetime
                new.end_datetime = bubble.end_datetime
                new.put()

                bubble.optional_bubbles.append(new.key())
                bubble.put()


            self.redirect('/bubble/%s' % new.key().id())


class AddExistingBubble(boRequestHandler):
    def post(self, key):
        if self.authorize('bubbler'):
            bubble = Bubble().get(key)
            existing = self.request.get('key').strip()

            if bubble and existing:
                bubble.optional_bubbles = AddToList(db.Key(existing), bubble.optional_bubbles)
                bubble.put()


class AddOptionalSubbubble(boRequestHandler):
    def get(self, parent_key, child_key):
        if self.authorize('bubbler'):
            parent = Bubble().get(parent_key)
            child = Bubble().get(child_key)

            if parent and child:
                parent.optional_bubbles = AddToList(db.Key(child_key), parent.optional_bubbles)
                parent.put()


class DeleteBubble(boRequestHandler):
    def get(self, key):
        if self.authorize('bubbler'):
            bubble = Bubble().get(key)
            if bubble:
                if bubble.bubbles:
                    self.redirect('/bubble/%s' % key)
                else:
                    bubble.is_deleted = True
                    bubble.put()
                    if bubble.in_bubbles:
                        self.redirect('/bubble/%s' % bubble.in_bubbles[0].key().id())


class DeleteFromBubble(boRequestHandler):
    def get(self, delete_bubble_key, from_bubble_key):
        if self.authorize('bubbler'):
            from_bubble = Bubble().get(from_bubble_key)
            if from_bubble:
                if db.Key(delete_bubble_key) in from_bubble.optional_bubbles:
                    from_bubble.optional_bubbles.remove(db.Key(delete_bubble_key))
                if db.Key(delete_bubble_key) in from_bubble.mandatory_bubbles:
                    from_bubble.mandatory_bubbles.remove(db.Key(delete_bubble_key))
                from_bubble.put()

            self.redirect('/bubble/%s' % from_bubble.key().id())


# TODO: This method should return seeders of current bubble.
# Right now it returns all persons in system. WTF
class GetSeeders(boRequestHandler):
    def get(self):
        if self.authorize('bubbler'):
            query = self.request.get('query').strip()
            keys = []
            names = []
            for p in db.Query(Person).filter('forename >=', query).order('forename').order('surname').fetch(100):
                keys.append(str(p.key()))
                names.append(p.displayname)
            respond = {
                'query': query,
                'suggestions': names,
                'data': keys
            }

            self.echo_json(respond)


class AddSeeder(boRequestHandler):
    def get(self, bubble_key, person_key):
        if self.authorize('bubbler'):
            bubble = Bubble().get(bubble_key)
            person = Person().get(person_key)
            if bubble and person:
                bubble.seeders = AddToList(person.key(), bubble.seeders)
                bubble.put()
                person.seeder = AddToList(bubble.key(), person.seeder)
                person.put()

            persons = {}
            for p in bubble.seeders2:
                persons[str(p.key())] = p.displayname
            self.echo_json(persons)


class AddLeecher(boRequestHandler):
    def get(self, bubble_key, person_key):
        if self.authorize('bubbler'):
            bubble = Bubble().get(bubble_key)
            person = Person().get(person_key)
            if bubble and person:
                person.add_leecher(bubble.key())

            persons = {}
            for p in bubble.leechers2:
                persons[str(p.key())] = p.displayname
            self.echo_json(persons)


class DeleteSeeder(boRequestHandler):
    def get(self, bubble_key, person_key):
        if self.authorize('bubbler'):
            bubble = Bubble().get(bubble_key)
            person = Person().get(person_key)
            if bubble and person:
                if bubble.key() in person.seeder:
                    person.seeder.remove(bubble.key())
                person.put()
                if person.key() in bubble.seeders:
                    bubble.seeders.remove(person.key())
                bubble.put()

            persons = {}
            for p in bubble.seeders2:
                persons[str(p.key())] = p.displayname
            self.echo_json(persons)


class DeleteLeecher(boRequestHandler):
    def get(self, bubble_key, person_key):
        if self.authorize('bubbler'):
            bubble = Bubble().get(bubble_key)
            person = Person().get(person_key)
            if bubble and person:
                person.remove_leecher(bubble.key())

            persons = {}
            for p in bubble.leechers2:
                persons[str(p.key())] = p.displayname
            self.echo_json(persons)


class AddTimeslots(boRequestHandler):
    def post(self, bubble_key):
        if self.authorize('bubbler'):
            start_str = self.request.get('start').strip()
            end_str = self.request.get('end').strip()
            interval_str = self.request.get('interval').strip()

            interval = int(interval_str)
            start = datetime.strptime(start_str, '%d.%m.%Y %H:%M')
            end = datetime.strptime(end_str, '%d.%m.%Y %H:%M')
            timeslot = start
            times = []

            bubble = Bubble().get(bubble_key)

            while timeslot < end:
                new = Bubble()
                new.type = 'personal_time_slot'
                new.name = DictionaryAdd('bubble_name', bubble.displayname + ' - Aeg')
                new.start_datetime = timeslot

                timeslot = timeslot + timedelta(minutes=interval)

                new.end_datetime = timeslot
                new.put()

                bubble.optional_bubbles.append(new.key())
                bubble.put()


class DeleteNextInLine(boRequestHandler):
    def post(self, bubble_key):
        if self.authorize('bubbler'):
            nextinline = self.request.get('nextinline').strip()

            bubble = Bubble().get(bubble_key)

            if bubble:
                bubble.next_in_line = RemoveFromList(db.Key(nextinline), bubble.next_in_line)
                bubble.put()


class DeletePrerequisite(boRequestHandler):
    def post(self, bubble_key):
        if self.authorize('bubbler'):
            prerequisite = self.request.get('prerequisite').strip()

            bubble = Bubble().get(bubble_key)

            if bubble:
                bubble.prerequisite_bubbles = RemoveFromList(db.Key(prerequisite), bubble.prerequisite_bubbles)
                bubble.put()


class SubBubblesCSV(boRequestHandler):
    def get(self, bubble_id):
        if self.authorize('bubbler'):
            bubble = Bubble().get_by_id(int(bubble_id))
            csvfile = cStringIO.StringIO()
            csvWriter = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)

            for b in sorted(bubble.bubbles, key=lambda k: k.start_datetime):
                csvWriter.writerow([
                    b.type2.displayname.encode("utf-8"),
                    b.displayname.encode("utf-8"),
                    b.displaydate.encode("utf-8"),
                    ', '.join([p.displayname.encode("utf-8") for p in b.leechers2])
                ])

            self.header('Content-Type', 'text/csv; charset=utf-8')
            self.header('Content-Disposition', 'attachment; filename=' + unicode(bubble.displayname.encode("utf-8"), errors='ignore') + '.csv')
            self.echo(csvfile.getvalue())
            csvfile.close()



def main():
    Route([
            (r'/bubble/show/(.*)', ShowBubble),
            (r'/bubble/add/(.*)/(.*)', AddBubble),
            (r'/bubble/add_existing/(.*)', AddExistingBubble),
            (r'/bubble/add_optional_subbubble/(.*)/(.*)', AddOptionalSubbubble),
            (r'/bubble/add_timeslot/(.*)', AddTimeslots),
            (r'/bubble/csv/(.*)', SubBubblesCSV),
            (r'/bubble/delete/(.*)', DeleteBubble),
            (r'/bubble/delete_from_bubble/(.*)/(.*)', DeleteFromBubble),
            (r'/bubble/delete_nextinline/(.*)', DeleteNextInLine),
            (r'/bubble/delete_prerequisite/(.*)', DeletePrerequisite),
            (r'/bubble/seeders', GetSeeders),
            (r'/bubble/seeder/add/(.*)/(.*)', AddSeeder),
            (r'/bubble/seeder/delete/(.*)/(.*)', DeleteSeeder),
            (r'/bubble/leecher/add/(.*)/(.*)', AddLeecher),
            (r'/bubble/leecher/delete/(.*)/(.*)', DeleteLeecher),
            (r'/bubble/(.*)', ShowBubbleList),
        ])


if __name__ == '__main__':
    main()