from google.appengine.api import users
from google.appengine.api import memcache
from datetime import *
import time
import re

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

        if self.request.get('flush', '').lower() == 'true':
            memcache.flush_all()

        for k, v in memcache.get_stats().iteritems():
            if k in ['bytes', 'byte_hits']:
                v = '%skB' % (v/1024)
            if k == 'oldest_item_age':
                v = '%smin' % (v/60)
            self.echo('%s: %s' % (k, v))


class FixStuff(boRequestHandler):
    def get(self):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        self.echo(str(db.Query(BubbleRelation).order('-_changed').count(limit=100000)))
        # taskqueue.Task(url='/update/stuff').add()

    def post(self):
        for b in db.Query(BubbleRelation).fetch(500):
            if hasattr(b, '_version'):
                setattr(b, 'x_version', b._version)
                delattr(b, '_version')
            if hasattr(b, '_created'):
                setattr(b, 'x_created', b._created)
                delattr(b, '_created')
            if hasattr(b, '_created_by'):
                setattr(b, 'x_created_by', b._created_by)
                delattr(b, '_created_by')
            if hasattr(b, '_changed'):
                setattr(b, 'x_changed', b._changed)
                delattr(b, '_changed')
            if hasattr(b, '_changed_by'):
                setattr(b, 'x_changed_by', b._changed_by)
                delattr(b, '_changed_by')
            if hasattr(b, '_is_deleted'):
                setattr(b, 'x_is_deleted', b._is_deleted)
                delattr(b, '_is_deleted')
            if hasattr(b, 'name'):
                delattr(b, 'name')
            if hasattr(b, 'name_plural'):
                delattr(b, 'name_plural')
            try:
                b.put()
            except:
                pass

        if db.Query(BubbleRelation).order('-_changed').count(limit=100000) > 0:
            taskqueue.Task(url='/update/stuff').add()


class AddUser(boRequestHandler):
    def get(self, type):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        for b in db.Query(Bubble).filter('type', type).fetch(1000):
            if hasattr(b, 'x_br_viewer'):
                b.x_br_viewer = AddToList(db.Key('agpzfmJ1YmJsZWR1cg8LEgZQZXJzb24Ykf2yAgw'), b.x_br_viewer)
            else:
                b.x_br_viewer = [db.Key('agpzfmJ1YmJsZWR1cg8LEgZQZXJzb24Ykf2yAgw')]
            b.x_br_viewer = AddToList(db.Key('agpzfmJ1YmJsZWR1cg8LEgZQZXJzb24Yq-2yAgw'), b.x_br_viewer)
            b.put()
            self.echo(str(b.key()))


class Check(boRequestHandler):
    def get(self):
        for b in db.Query(Bubble).filter('type', 'bubble_type').fetch(1000):
            keys = getattr(b, 'bubble_properties', [])
            if type(keys) is not list:
                keys = [keys]

            for k in keys:
                try:
                    bb = Bubble().get(k)
                except:
                    b.bubble_properties = RemoveFromList(k, b.bubble_properties)
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

            bubble.x_br_viewer = [db.Key('agpzfmJ1YmJsZWR1cg8LEgZQZXJzb24Ykf2yAgw'), db.Key('agpzfmJ1YmJsZWR1cg8LEgZQZXJzb24Yq-2yAgw')]
            bubble.put()

            # bubble.viewer
            for related_bubble in db.Query(Bubble).filter('x_br_viewer', person.key()).fetch(1000):
                if not db.Query(BubbleRelation).filter('bubble', related_bubble).filter('related_bubble', bubble).filter('type', 'viewer').get():
                    br = BubbleRelation()
                    br.bubble = related_bubble.key()
                    br.related_bubble = bubble.key()
                    br.type = 'seeder'
                    br.put()

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



class BubbleType2Bubble(boRequestHandler):
    def get(self):
        taskqueue.Task(url='/update/bt2b').add()
        self.echo('OK')

    def post(self):
        # for b in db.Query(Bubble).filter('type', 'bubble_type').fetch(1000):
        #     if hasattr(b, 'allowed_subtypes'):
        #         if type(b.allowed_subtypes) is not list:
        #             b.allowed_subtypes = [b.allowed_subtypes]
        #         for v in b.allowed_subtypes:
        #             ab = db.Query(Bubble).filter('type', 'bubble_type').filter('path', v).get()
        #             if ab:
        #                 b.allowed_subtypes = AddToList(ab.key(), b.allowed_subtypes)
        #                 b.allowed_subtypes = RemoveFromList(v, b.allowed_subtypes)

        #         if len(b.allowed_subtypes) == 1:
        #             b.allowed_subtypes = b.allowed_subtypes[0]
        #         b.put()

        b = Bubble().get('agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYh-6yAgw')
        b.optional_bubbles = MergeLists(db.Query(Bubble, keys_only=True).filter('type', 'bubble_type').fetch(1000), db.Query(Bubble, keys_only=True).filter('type', 'bubble_property').fetch(1000))
        b.put()


def main():
    Route([
            ('/update/docs', Dokumendid),
            ('/update/cache', MemCacheInfo),
            ('/update/stuff', FixStuff),
            ('/update/p2b', Person2Bubble),
            ('/update/bt2b', BubbleType2Bubble),
            ('/update/check', Check),
            (r'/update/user/(.*)', AddUser),
        ])


if __name__ == '__main__':
    main()
