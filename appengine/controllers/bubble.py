from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

from operator import attrgetter

import string
import csv
import cStringIO
import urllib
from datetime import *

from bo import *
from database.bubble import *
from database.person import *
from database.dictionary import *


class ShowBubbleList(boRequestHandler):
    def get(self, bubbletype = None):
        bt = db.Query(BubbleType).filter('type', bubbletype.strip('/')).get()

        self.view(
            main_template='main/index.html',
            template_file = 'main/list.html',
            page_title = bt.name_plural.value if bt else None,
            values = {
                'list_url': '/bubble%s' % bubbletype,
                'content_url': '/bubble/show',
            }
        )

    def post(self, bubbletype = None):
        key = self.request.get('key').strip()
        if key:
            bubble = Bubble().get(key)
            if not bubble.Authorize('viewer'):
                self.error(404)
                return

            bubble.AutoFix()

            self.echo_json({
                'id': bubble.key().id(),
                'key': str(bubble.key()),
                'image': bubble.GetPhotoUrl(32),
                'title': bubble.displayname,
                'info': bubble.displayinfo,
                'type': bubble.type,
                'type_name': bubble.GetType().displayname,
            })
            return

        keys = None
        bubbletype = bubbletype.strip('/')
        search = self.request.get('search').strip().lower()

        leecher_in_bubble = self.request.get('leecher_in_bubble').strip()
        bubble_leechers = self.request.get('bubble_leechers').strip()

        master_bubble = self.request.get('master_bubble').strip()
        btype = self.request.get('type').strip()

        if search:
            keys = [str(k) for k in list(db.Query(Bubble, keys_only=True).filter('viewers', Person().current.key()).filter('type', bubbletype).filter('search_'+UserPreferences().current.language, search).filter('_is_deleted', False).order('sort_'+UserPreferences().current.language))]

        if bubbletype and not search:
            keys = [str(k) for k in list(db.Query(Bubble, keys_only=True).filter('viewers', Person().current.key()).filter('type', bubbletype).filter('_is_deleted', False).order('sort_'+UserPreferences().current.language))]

        if leecher_in_bubble:
            keys = [str(b.bubble.key()) for b in db.Query(BubbleRelation).filter('related_bubble', db.Key(leecher_in_bubble)).filter('type', 'leecher').filter('_is_deleted', False)]

        if bubble_leechers:
            keys = [str(b.related_bubble.key()) for b in db.Query(BubbleRelation).filter('bubble', db.Key(bubble_leechers)).filter('type', 'leecher').filter('_is_deleted', False) if b.related_bubble.Authorize('viewer')]

        if master_bubble:
            bubble = Bubble().get(master_bubble)
            keys = [str(b.key()) for b in sorted(Bubble().get(bubble.subbubbles), key=attrgetter('_created'), reverse=True) if b.type == btype and b.Authorize('viewer')]

        self.echo_json({'keys': keys})


class ShowBubble(boRequestHandler):
    def get(self, bubble_id):
        bubble = Bubble().get_by_id(int(bubble_id))
        if not bubble.Authorize('viewer'):
            self.error(404)
            return

        bubble.photourl = bubble.GetPhotoUrl(150)
        self.view(
            main_template = 'main/index.html',
            template_file = 'bubble/info.html',
            page_title = bubble.displayname,
            values = {
                'bubble': bubble,
                'bubbletypes': db.Query(BubbleType).fetch(50)
            }
        )


class ShowBubbleXML(boRequestHandler):
    def get(self, bubble_id):
        bubble = Bubble().get_by_id(int(bubble_id))
        if not bubble.Authorize('viewer'):
            self.error(404)
            return

        self.header('Content-Type', 'text/xml')
        self.echo(bubble.to_xml())


class EditBubble(boRequestHandler):
    def get(self, bubble_id):
        bubble = Bubble().get_by_id(int(bubble_id))
        if not bubble.Authorize('viewer'):
            self.error(404)
            return

        self.view(
            main_template = '',
            template_file = 'bubble/edit.html',
            values = {
                'bubble': bubble,
                'blobstore_upload_url': blobstore.create_upload_url('/bubble/upload_file/%s' % bubble_id),
            }
        )

    def post(self, bubble_id):
        bubble = Bubble().get_by_id(int(bubble_id))
        if not bubble.Authorize('viewer'):
            self.error(404)
            return

        value = bubble.SetProperty(
            propertykey = self.request.get('property').strip(),
            oldvalue = self.request.get('oldvalue').strip(),
            newvalue = self.request.get('newvalue').strip(),
        )
        self.echo(value, False)


class AddBubble(boRequestHandler):
    def post(self, bubble_id):
        bubble = Bubble().get_by_id(int(bubble_id))
        if not bubble.Authorize('viewer'):
            self.error(404)
            return

        newbubble = bubble.AddSubbubble(self.request.get('type').strip())
        self.echo(newbubble.key().id(), False)


class DownloadBubbleFile(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, data_property, file_key=None):
        b = blobstore.BlobInfo.get(urllib.unquote(file_key))
        if not b:
            self.error(404)
            return

        bubble = db.Query(Bubble).filter(data_property, b.key()).get()
        if not bubble:
            self.error(404)
            return

        if not bubble.Authorize('viewer'):
            self.error(404)
            return

        self.send_blob(b, save_as = ReplaceUTF(b.filename))


class UploadBubbleFile(blobstore_handlers.BlobstoreUploadHandler):
    def post(self, bubble_id):
        bubble = Bubble().get_by_id(int(bubble_id))
        if not bubble.Authorize('viewer'):
            self.error(404)
            return

        upload_files = self.get_uploads('file')
        if not upload_files:
            return

        blob_info = upload_files[0]

        value = bubble.SetProperty(
            propertykey = self.request.get('property').strip(),
            newvalue = blob_info.key(),
        )

        self.response.out.write(blob_info.filename)


class ShowBubbleDoc1(boRequestHandler):
    def get(self, id):
        bubble = Bubble().get_by_id(int(id))
        if not bubble.Authorize('viewer'):
            self.error(404)
            return

        leechers = bubble.GetLeechers()
        for l in leechers:
            l.group = []
            for g in db.Query(Bubble).filter('mandatory_bubbles', bubble.key()).filter('leechers', l.key()):
                tags = g.GetTypedTags()
                if 'code' in tags:
                    l.group.append(g.GetTypedTags()['code'])

        self.view(
            main_template = 'main/print.html',
            template_file = 'bubble/doc1.html',
            values = {
                'bubble': bubble,
                'leechers': leechers,
                'date': datetime.today(),
            }
        )












# class ShowBubble1(boRequestHandler):
#     def get(self, id):
#         if self.authorize('bubbler'):

#             bubble = Bubble().get_by_id(int(id))
#             bubble_key = bubble.key()

# #            nextinline_bubbles = []
# #            for mb in bubble.InBubbles:
# #                nextinline_bubbles.append(mb)
# #                for mb2 in mb.SubBubbles:
# #                    if mb2.key() != bubble.key():
# #                        nextinline_bubbles.append(mb2)
# #                    mb2_subbubbles = mb2.SubBubbles
# #                    if mb2_subbubbles:
# #                        nextinline_bubbles.extend(mb2_subbubbles)

#             nextinline_bubbles_d = {}

#             in_bubbles_d = bubble.InBubblesD
#             nextinline_bubbles_d.update( in_bubbles_d )

#             for in_bubble in in_bubbles_d.values():
#                 sibling_bubbles_d = in_bubble.SubBubblesD
#                 nextinline_bubbles_d.update( sibling_bubbles_d )

#                 for sibling_bubble in sibling_bubbles_d.values():
#                     child_bubbles_d = sibling_bubble.SubBubblesD
#                     nextinline_bubbles_d.update( child_bubbles_d )

#             nextinline_bubbles_d[bubble_key] = 'foo'
#             del nextinline_bubbles_d[bubble_key]

#             nextinline_bubbles = nextinline_bubbles_d.values()

#             ratingscales = db.Query(RatingScale).fetch(1000)

#             #addable_bubbles = db.Query(Bubble).filter('__key__ !=', bubble.key()).filter('type IN', bubble.type2.allowed_subtypes).filter('_is_deleted', False).fetch(1000)
#             addable_bubbles = nextinline_bubbles
#             prerequisite_bubbles = nextinline_bubbles

#             changeinfo = ''
#             last_change = bubble.last_change
#             if last_change:
#                 if last_change.user:
#                     changer = db.Query(Person).filter('user', last_change.user).get()
#                     if changer:
#                         changeinfo = Translate('bubble_changed_on') % {'name': changer.displayname, 'date': UtcToLocalDateTime(last_change.datetime).strftime('%d.%m.%Y %H:%M')}

#             self.view(bubble.type2.displayname + ' - ' + bubble.displayname, 'bubble/bubble.html', {
#                 'bubble': bubble,
#                 'changed': changeinfo,
#                 'ratingscales': ratingscales,
#                 'addable_bubbles': addable_bubbles,
#                 'nextinline_bubbles': nextinline_bubbles,
#                 'prerequisite_bubbles': prerequisite_bubbles,
#             })

#     def post(self, key):
#         if self.authorize('bubbler'):
#             bubble = Bubble().get(key)
#             field = self.request.get('field').strip()
#             value = self.request.get('value').strip()
#             if bubble:
#                 if value:
#                     if field in ['name', 'description', 'badge']:
#                         setattr(bubble, field, DictionaryAdd(('bubble_' + field), value))
#                         if field == 'name':
#                             bubble.sort_estonian = StringToSortable(value)
#                     if field in ['start_datetime', 'end_datetime']:
#                         setattr(bubble, field, datetime.strptime(value, '%d.%m.%Y %H:%M'))
#                     if field == 'rating_scale':
#                         bubble.rating_scale = db.Key(value)
#                     if field == 'maximum_leecher_count':
#                         bubble.maximum_leecher_count = int(value)
#                     if field == 'url':
#                         bubble.url = value
#                     if field == 'nextinline':
#                         bubble.next_in_line = AddToList(db.Key(value), bubble.next_in_line)
#                     if field == 'prerequisite':
#                         bubble.prerequisite_bubbles = AddToList(db.Key(value), bubble.prerequisite_bubbles)
#                     if field == 'is_mandatory':
#                         subbubble = self.request.get('subbubble').strip()
#                         if subbubble:
#                             if value.lower() == 'true':
#                                 bubble.mandatory_bubbles = AddToList(db.Key(subbubble), bubble.mandatory_bubbles)
#                                 bubble.optional_bubbles = RemoveFromList(db.Key(subbubble), bubble.optional_bubbles)
#                                 taskqueue.Task(url='/taskqueue/bubble_copy_leechers', params={'from_bubble_key': str(bubble.key()), 'to_bubble_key': subbubble}).add(queue_name='one-by-one')
#                             else:
#                                 bubble.optional_bubbles = AddToList(db.Key(subbubble), bubble.optional_bubbles)
#                                 bubble.mandatory_bubbles = RemoveFromList(db.Key(subbubble), bubble.mandatory_bubbles)
#                 else:
#                     setattr(bubble, field, None)

#                 bubble.put()
#                 bubble.displayname_cache_reset()


# class AddBubble(boRequestHandler):
#     def get(self, type, key):
#         if self.authorize('bubbler'):
#             bubble = Bubble().get(key)
#             if bubble:

#                 new = Bubble()
#                 new.type = type
#                 new.name = DictionaryAdd('bubble_name', '')
#                 new.start_datetime = bubble.start_datetime
#                 new.end_datetime = bubble.end_datetime
#                 new.put()

#                 bubble.optional_bubbles.append(new.key())
#                 bubble.put()


#             self.redirect('/bubble/%s' % new.key().id())


# class AddExistingBubble(boRequestHandler):
#     def post(self, key):
#         if self.authorize('bubbler'):
#             bubble = Bubble().get(key)
#             existing = self.request.get('key').strip()

#             if bubble and existing:
#                 bubble.optional_bubbles = AddToList(db.Key(existing), bubble.optional_bubbles)
#                 bubble.put()


# class AddOptionalSubbubble(boRequestHandler):
#     def get(self, parent_key, child_key):
#         if self.authorize('bubbler'):
#             parent = Bubble().get(parent_key)
#             child = Bubble().get(child_key)

#             if parent and child:
#                 parent.optional_bubbles = AddToList(db.Key(child_key), parent.optional_bubbles)
#                 parent.put()


# class DeleteBubble(boRequestHandler):
#     def get(self, key):
#         if self.authorize('bubbler'):
#             bubble = Bubble().get(key)
#             if bubble:
#                 if bubble.bubbles:
#                     self.redirect('/bubble/%s' % key)
#                 else:
#                     bubble._is_deleted = True
#                     bubble.put()
#                     if bubble.in_bubbles:
#                         self.redirect('/bubble/%s' % bubble.in_bubbles[0].key().id())


# class DeleteFromBubble(boRequestHandler):
#     def get(self, delete_bubble_key, from_bubble_key):
#         if self.authorize('bubbler'):
#             from_bubble = Bubble().get(from_bubble_key)
#             if from_bubble:
#                 if db.Key(delete_bubble_key) in from_bubble.optional_bubbles:
#                     from_bubble.optional_bubbles.remove(db.Key(delete_bubble_key))
#                 if db.Key(delete_bubble_key) in from_bubble.mandatory_bubbles:
#                     from_bubble.mandatory_bubbles.remove(db.Key(delete_bubble_key))
#                 from_bubble.put()

#             self.redirect('/bubble/%s' % from_bubble.key().id())


# # TODO: This method should return seeders of current bubble.
# # Right now it returns all persons in system. WTF
# class GetSeeders(boRequestHandler):
#     def get(self):
#         if self.authorize('bubbler'):
#             query = self.request.get('query').strip()
#             keys = []
#             names = []
#             for p in db.Query(Person).filter('forename >=', query).order('forename').order('surname').fetch(100):
#                 keys.append(str(p.key()))
#                 names.append(p.displayname)
#             respond = {
#                 'query': query,
#                 'suggestions': names,
#                 'data': keys
#             }

#             self.echo_json(respond)


# class AddSeeder(boRequestHandler):
#     def get(self, bubble_key, person_key):
#         if self.authorize('bubbler'):
#             bubble = Bubble().get(bubble_key)
#             person = Person().get(person_key)
#             if bubble and person:
#                 bubble.seeders = AddToList(person.key(), bubble.seeders)
#                 bubble.put()
#                 person.seeder = AddToList(bubble.key(), person.seeder)
#                 person.put()

#             persons = {}
#             for p in bubble.seeders2:
#                 persons[str(p.key())] = p.displayname
#             self.echo_json(persons)


# class AddLeecher(boRequestHandler):
#     def get(self, bubble_key, person_key):
#         if self.authorize('bubbler'):
#             bubble = Bubble().get(bubble_key)
#             person = Person().get(person_key)
#             if bubble and person:
#                 person.add_leecher(bubble.key())

#             persons = {}
#             for p in bubble.leechers2:
#                 persons[str(p.key())] = p.displayname
#             self.echo_json(persons)


# class DeleteSeeder(boRequestHandler):
#     def get(self, bubble_key, person_key):
#         if self.authorize('bubbler'):
#             bubble = Bubble().get(bubble_key)
#             person = Person().get(person_key)
#             if bubble and person:
#                 if bubble.key() in person.seeder:
#                     person.seeder.remove(bubble.key())
#                 person.put()
#                 if person.key() in bubble.seeders:
#                     bubble.seeders.remove(person.key())
#                 bubble.put()

#             persons = {}
#             for p in bubble.seeders2:
#                 persons[str(p.key())] = p.displayname
#             self.echo_json(persons)


# class DeleteLeecher(boRequestHandler):
#     def get(self, bubble_key, person_key):
#         if self.authorize('bubbler'):
#             bubble = Bubble().get(bubble_key)
#             person = Person().get(person_key)
#             if bubble and person:
#                 person.remove_leecher(bubble.key())

#             persons = {}
#             for p in bubble.leechers2:
#                 persons[str(p.key())] = p.displayname
#             self.echo_json(persons)


# class AddTimeslots(boRequestHandler):
#     def post(self, bubble_key):
#         if self.authorize('bubbler'):
#             start_str = self.request.get('start').strip()
#             end_str = self.request.get('end').strip()
#             interval_str = self.request.get('interval').strip()

#             interval = int(interval_str)
#             start = datetime.strptime(start_str, '%d.%m.%Y %H:%M')
#             end = datetime.strptime(end_str, '%d.%m.%Y %H:%M')
#             timeslot = start
#             times = []

#             bubble = Bubble().get(bubble_key)

#             while timeslot < end:
#                 new = Bubble()
#                 new.type = 'personal_time_slot'
#                 new.name = DictionaryAdd('bubble_name', bubble.displayname + ' - Aeg')
#                 new.start_datetime = timeslot

#                 timeslot = timeslot + timedelta(minutes=interval)

#                 new.end_datetime = timeslot
#                 new.put()

#                 bubble.optional_bubbles.append(new.key())
#                 bubble.put()


# class DeleteNextInLine(boRequestHandler):
#     def post(self, bubble_key):
#         if self.authorize('bubbler'):
#             nextinline = self.request.get('nextinline').strip()

#             bubble = Bubble().get(bubble_key)

#             if bubble:
#                 bubble.next_in_line = RemoveFromList(db.Key(nextinline), bubble.next_in_line)
#                 bubble.put()


# class DeletePrerequisite(boRequestHandler):
#     def post(self, bubble_key):
#         if self.authorize('bubbler'):
#             prerequisite = self.request.get('prerequisite').strip()

#             bubble = Bubble().get(bubble_key)

#             if bubble:
#                 bubble.prerequisite_bubbles = RemoveFromList(db.Key(prerequisite), bubble.prerequisite_bubbles)
#                 bubble.put()


# class SubBubblesCSV(boRequestHandler):
#     def get(self, bubble_id):
#         if self.authorize('bubbler'):
#             bubble = Bubble().get_by_id(int(bubble_id))
#             csvfile = cStringIO.StringIO()
#             csvWriter = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)

#             for b in sorted(bubble.bubbles, key=lambda k: k.start_datetime):
#                 csvWriter.writerow([
#                     b.type2.displayname.encode("utf-8"),
#                     b.displayname.encode("utf-8"),
#                     b.displaydate.encode("utf-8"),
#                     ', '.join([p.displayname.encode("utf-8") for p in b.leechers2])
#                 ])

#             self.header('Content-Type', 'text/csv; charset=utf-8')
#             self.header('Content-Disposition', 'attachment; filename=' + unicode(bubble.displayname.encode("utf-8"), errors='ignore') + '.csv')
#             self.echo(csvfile.getvalue())
#             csvfile.close()


# class Leech(boRequestHandler):
#     def get(self, bubble_key):
#         bubble = Bubble().get(bubble_key)
#         person = Person().current

#         bubbles = []
#         for b in bubble.bubbles:
#             if db.Query(BubblePerson).filter('bubble', b).filter('person', person).filter('status', 'waiting').get() or person.key() in b.leechers:
#                 b.selected = True
#             if b.maximum_leecher_count:
#                 b.free_count = b.maximum_leecher_count - (len(b.leechers) + db.Query(BubblePerson).filter('bubble', b).filter('status', 'waiting').count())
#             bubbles.append(b)

#         self.view(bubble.displayname, 'bubble/leeching.html', {
#             'bubble': bubble,
#             'bubbles': bubbles,
#         })

#     def post(self, bubble_key = None):
#         bubble_key = db.Key(self.request.get('key').strip())
#         person = Person().current

#         if self.request.get('leech').strip().lower() == 'true':
#             if not db.Query(BubblePerson).filter('bubble', bubble_key).filter('person', person).filter('status', 'waiting').get():
#                 bp = BubblePerson()
#                 bp.bubble = bubble_key
#                 bp.person = Person().current
#                 bp.status = 'waiting'
#                 bp.put()
#         else:
#             bp = db.Query(BubblePerson).filter('bubble', bubble_key).filter('person', person).filter('status', 'waiting').get()
#             if bp:
#                 bp.status = 'canceled'
#                 bp.put()


def main():
    Route([
            (r'/bubble/show/(.*)', ShowBubble),
            (r'/bubble/edit/(.*)', EditBubble),
            (r'/bubble/add/(.*)', AddBubble),
            (r'/bubble/file/(.*)/(.*)', DownloadBubbleFile),
            (r'/bubble/upload_file/(.*)', UploadBubbleFile),
            (r'/bubble/d1/(.*)', ShowBubbleDoc1),
            (r'/bubble/xml/(.*)', ShowBubbleXML),
            # (r'/bubble/add/(.*)/(.*)', AddBubble),
            # (r'/bubble/add_existing/(.*)', AddExistingBubble),
            # (r'/bubble/add_optional_subbubble/(.*)/(.*)', AddOptionalSubbubble),
            # (r'/bubble/add_timeslot/(.*)', AddTimeslots),
            # (r'/bubble/csv/(.*)', SubBubblesCSV),
            # (r'/bubble/delete/(.*)', DeleteBubble),
            # (r'/bubble/delete_from_bubble/(.*)/(.*)', DeleteFromBubble),
            # (r'/bubble/delete_nextinline/(.*)', DeleteNextInLine),
            # (r'/bubble/delete_prerequisite/(.*)', DeletePrerequisite),
            # (r'/bubble/seeders', GetSeeders),
            # (r'/bubble/seeder/add/(.*)/(.*)', AddSeeder),
            # (r'/bubble/seeder/delete/(.*)/(.*)', DeleteSeeder),
            # (r'/bubble/leecher/add/(.*)/(.*)', AddLeecher),
            # (r'/bubble/leecher/delete/(.*)/(.*)', DeleteLeecher),
            # (r'/bubble/leech/(.*)', Leech),
            (r'/bubble(.*)', ShowBubbleList),
        ])


if __name__ == '__main__':
    main()
