from google.appengine.api import users
from google.appengine.api import memcache
from datetime import *
import time

from bo import *
from database.bubble import *
from database.person import *
from database.feedback import *
from database.zimport.zoin import *
from database.zimport.zbubble import *


class Dokumendid(boRequestHandler):
    def get(self):
        taskqueue.Task(url='/update/docs').add()

    def post(self):
        csv = []
        for c in db.Query(Counter).order('__key__').fetch(1000):
            for b in db.Query(Bubble).filter('registry_number_counter', c.key()).fetch(1000):
                if len(getattr(b, 'optional_bubbles', [])) > 0:
                    for sb in Bubble().get(b.optional_bubbles):
                        if sb:
                            csv.append('%s;%s;%s;%s;%s' % (c.displayname, sb.type, sb.key().id(), getattr(sb, 'registry_number', ''), sb.displayname))

        SendMail(
            to = 'argo.roots@artun.ee',
            subject = 'Docs',
            message = 'jee',
            attachments = [('Docs.csv', '\n'.join(csv))],
        )


class MemCacheInfo(boRequestHandler):
    def get(self):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        for k, v in memcache.get_stats().iteritems():
            if k in ['bytes', 'byte_hits']:
                v = '%skB' % (v/1024)
            if k == 'oldest_item_age':
                v = '%smin' % (v/60)
            self.echo('%s: %s' % (k, v))


class FixStuff(boRequestHandler):
    def get(self):
        # taskqueue.Task(url='/update/stuff').add()

        b = Bubble().get('agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYtPewAgw')
        b.optional_bubbles = AddToList(db.Key('agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUY2-i3Agw'), b.optional_bubbles)
        b.put()

        b = Bubble().get('agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYoYCyAgw')
        b.optional_bubbles = RemoveFromList(db.Key('agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUY2-i3Agw'), b.optional_bubbles)
        b.put()


    def post(self):
        # b = Bubble().get('agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYjcmwAgw')
        # b.optional_bubbles = AddToList(db.Key('agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYy4S1Agw'), b.optional_bubbles)
        # b.put()

        # b = Bubble().get('agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYrNuyAgw')
        # b.optional_bubbles = AddToList(db.Key('agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYnP20Agw'), b.optional_bubbles)
        # b.optional_bubbles = AddToList(db.Key('agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYwKe0Agw'), b.optional_bubbles)
        # b.put()

        for b in db.Query(Bubble).filter('allowed_subtypes', 'doc_kirjavahetus').fetch(1000):
            b.reply_counter = db.Key('agpzfmJ1YmJsZWR1chALEgdDb3VudGVyGK30twIM')
            b.put()
            # bt = b.GetType()
            # for pp_key in getattr(bt, 'propagated_properties', []):
            #     pp = BubbleProperty().get(pp_key)
            #     for sb in Bubble().get(b.optional_bubbles):
            #         if not hasattr(sb, pp.data_property):
            #             setattr(sb, pp.data_property, getattr(b, pp.data_property))
            #         sb.put()


class AddUser(boRequestHandler):
    def get(self, type):
        for b in db.Query(Bubble).filter('type', type).fetch(1000):
            if hasattr(b, 'viewers'):
                b.viewers = AddToList(db.Key('agpzfmJ1YmJsZWR1cg8LEgZQZXJzb24Ykf2yAgw'), b.viewers)
            else:
                b.viewers = [db.Key('agpzfmJ1YmJsZWR1cg8LEgZQZXJzb24Ykf2yAgw')]
                self.echo(str(b.key()))
            b.put()


class Person2Bubble(boRequestHandler):
    def get(self):
        taskqueue.Task(url='/update/p2b').add()


    def post(self):

        rc = 0
        limit = 100
        step = int(self.request.get('step', 1))
        offset = int(self.request.get('offset', 0))

        for person in db.Query(Person).filter('is_guest', False).order('__key__').fetch(limit=limit, offset=offset):
            rc += 1
            bubble = None
            if hasattr(person, 'person2bubble'):
                bubble = Bubble().get(person.person2bubble)

            if not bubble:
                bubble = Bubble()
                bubble.type = 'person'
                bubble.put()

            person.person2bubble = bubble.key()
            person.put()

            if getattr(person, 'forename', None):
                bubble.forename   = person.forename
            if getattr(person, 'surname', None):
                bubble.surname    = person.surname
            if getattr(person, 'users', None):
                bubble.users      = person.users
            if getattr(person, 'idcode', None):
                bubble.id_code    = person.idcode
            if getattr(person, 'gender', None):
                if person.gender.lower() == 'male':
                    bubble.gender = db.Key('agpzfmJ1YmJsZWR1chMLEgpEaWN0aW9uYXJ5GJ2tsAIM')
                if person.gender.lower() == 'female':
                    bubble.gender = db.Key('agpzfmJ1YmJsZWR1chMLEgpEaWN0aW9uYXJ5GJyGsAIM')
            if getattr(person, 'birth_date', None):
                bubble.birth_date = datetime(*(person.birth_date.timetuple()[:6]))

            bubble.viewers = [db.Key('agpzfmJ1YmJsZWR1cg8LEgZQZXJzb24Ykf2yAgw'), db.Key('agpzfmJ1YmJsZWR1cg8LEgZQZXJzb24Yq-2yAgw')]
            bubble.put()

            # bubble.seeder
            for related_bubble in Bubble().get(person.seeder):
                if not db.Query(BubbleRelation).filter('bubble', related_bubble).filter('related_bubble', bubble).filter('type', 'seeder').get():
                    br = BubbleRelation()
                    br.bubble = related_bubble.key()
                    br.related_bubble = bubble.key()
                    br.type = 'seeder'
                    br.put()

            # bubble.leecher
            for related_bubble in Bubble().get(person.leecher):
                if not db.Query(BubbleRelation).filter('bubble', related_bubble).filter('related_bubble', bubble).filter('type', 'leecher').get():
                    br = BubbleRelation()
                    br.bubble = related_bubble.key()
                    br.related_bubble = bubble.key()
                    br.type = 'leecher'
                    br.put()

            # QuestionaryPerson
            for qp in db.Query(QuestionaryPerson).filter('person', person.key()).fetch(1000):
                qp.person_b = bubble.key()
                qp.put()

            # QuestionAnswer.person
            for qa in db.Query(QuestionAnswer).filter('person', person.key()).fetch(1000):
                qa.person_b = bubble.key()
                qa.put()

            # QuestionAnswer.target_person
            for qa in db.Query(QuestionAnswer).filter('target_person', person.key()).fetch(1000):
                qa.target_person_b = bubble.key()
                qa.put()

        if rc == limit:
            taskqueue.Task(url='/update/p2b', params={'offset': (offset + rc), 'step': (step + 1)}).add()



def main():
    Route([
            ('/update/docs', Dokumendid),
            ('/update/cache', MemCacheInfo),
            ('/update/stuff', FixStuff),
            ('/update/p2b', Person2Bubble),
            (r'/update/user/(.*)', AddUser),
        ])


if __name__ == '__main__':
    main()
