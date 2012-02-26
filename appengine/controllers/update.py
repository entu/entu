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
        self.echo(str(db.Query(BubbleRelation).count(limit=1000000)))
        # taskqueue.Task(url='/update/stuff').add()

        bt = db.Query(Bubble).filter('path', 'person').get()
        b = Bubble().get('agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYy_rLAgw')
        b.x_type = bt.key()
        b.put()

    def post(self):
        pass

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


class Person2Bubble(boRequestHandler):
    def get(self):
        taskqueue.Task(url='/update/p2b').add()
        self.echo(str(db.Query(Person).filter('is_guest', False).order('__key__').count(limit=100000)))


    def post(self):
        rc = 0
        limit = 5
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
                bubble.forename = person.forename
            if getattr(person, 'surname', None):
                bubble.surname = person.surname
            if getattr(person, 'users', None):
                bubble.user = person.users
            if getattr(person, 'idcode', None):
                bubble.id_code = person.idcode
            if getattr(person, 'gender', None):
                if person.gender.lower() == 'male':
                    bubble.gender = db.Key('agpzfmJ1YmJsZWR1chMLEgpEaWN0aW9uYXJ5GJ2tsAIM')
                if person.gender.lower() == 'female':
                    bubble.gender = db.Key('agpzfmJ1YmJsZWR1chMLEgpEaWN0aW9uYXJ5GJyGsAIM')
            if getattr(person, 'birth_date', None):
                bubble.birth_date = datetime(*(person.birth_date.timetuple()[:6]))

            if hasattr(bubble, 'users'):
                delattr(bubble, 'users')

            bubble.x_br_viewer = [db.Key('agpzfmJ1YmJsZWR1cg8LEgZQZXJzb24Ykf2yAgw'), db.Key('agpzfmJ1YmJsZWR1cg8LEgZQZXJzb24Yq-2yAgw')]
            bubble.put()

            # bubble.viewer
            br = None
            for related_bubble in db.Query(Bubble).filter('x_br_viewer', person.key()).fetch(2000):
                br = db.Query(BubbleRelation).filter('bubble', related_bubble).filter('related_bubble', bubble).filter('type', 'viewer').get()
                if not br:
                    br = BubbleRelation()
                    br.bubble = related_bubble.key()
                    br.related_bubble = bubble.key()
                    br.type = 'viewer'
                    br.put()
                else:
                    if br.x_is_deleted != False:
                        br.x_is_deleted = False
                        br.put()

            # bubble.seeder
            br = None
            for related_bubble in Bubble().get(person.seeder):
                br = db.Query(BubbleRelation).filter('bubble', related_bubble).filter('related_bubble', bubble).filter('type', 'seeder').get()
                if not br:
                    br = BubbleRelation()
                    br.bubble = related_bubble.key()
                    br.related_bubble = bubble.key()
                    br.type = 'seeder'
                    br.put()
                else:
                    if br.x_is_deleted != False:
                        br.x_is_deleted = False
                        br.put()

            # bubble.leecher
            br = None
            for related_bubble in Bubble().get(person.leecher):
                br = db.Query(BubbleRelation).filter('bubble', related_bubble).filter('related_bubble', bubble).filter('type', 'leecher').get()
                if not br:
                    br = BubbleRelation()
                    br.bubble = related_bubble.key()
                    br.related_bubble = bubble.key()
                    br.type = 'leecher'
                    br.put()
                else:
                    if br.x_is_deleted != False:
                        br.x_is_deleted = False
                        br.put()

        logging.debug('#' + str(step) + ' - ' + str(rc) + ' rows from ' + str(offset))

        if rc == limit:
            taskqueue.Task(url='/update/p2b', params={'offset': (offset + rc), 'step': (step + 1)}).add()


class FixRelations(boRequestHandler):
    def get(self, type):
        taskqueue.Task(url='/update/relations/%s' % type).add()
        self.echo(str(db.Query(BubbleRelation).filter('type', type).filter('x_is_deleted', False).count(limit=100000)))
        self.echo(str(db.Query(BubbleRelation).filter('type', type).filter('x_is_deleted', True).count(limit=100000)))


    def post(self, type):
        rc = 0
        limit = 500
        step = int(self.request.get('step', 1))
        offset = int(self.request.get('offset', 0))

        for br in db.Query(BubbleRelation).filter('type', type).filter('x_is_deleted', False).order('__key__').fetch(limit=limit, offset=offset):
            rc += 1
            try:
                bubble = br.bubble
                setattr(bubble, 'x_br_%s' % type, MergeLists(getattr(bubble, 'x_br_%s' % type, []), br.related_bubble.key()))
                bubble.put()
            except:
                pass
        logging.debug('#' + str(step) + ' - ' + type + ' - ' + str(rc) + ' rows from ' + str(offset))

        if rc == limit:
            taskqueue.Task(url='/update/relations/%s' % type, params={'offset': (offset + rc), 'step': (step + 1)}).add()


class FixRelations2(boRequestHandler):
    def get(self, bubbletype, relationtype):
        taskqueue.Task(url='/update/relations2/%s/%s' % (bubbletype, relationtype)).add()
        self.echo(str(db.Query(Bubble).filter('type', bubbletype).filter('x_is_deleted', False).count(limit=100000)))
        self.echo(str(db.Query(Bubble).filter('type', bubbletype).filter('x_is_deleted', True).count(limit=100000)))


    def post(self, bubbletype, relationtype):
        rc = 0
        limit = 200
        step = int(self.request.get('step', 1))
        offset = int(self.request.get('offset', 0))

        for bubble in db.Query(Bubble).filter('type', bubbletype).order('__key__').fetch(limit=limit, offset=offset):
            rc += 1
            for r in getattr(bubble, 'x_br_%s' % relationtype, []):
                p = db.get(r)
                if p.kind() == 'Person':
                    if hasattr(p, 'person2bubble'):
                        setattr(bubble, 'x_br_%s' % relationtype, MergeLists(getattr(bubble, 'x_br_%s' % relationtype, []), p.person2bubble))
                        bubble.put()

        logging.debug('#' + str(step) + ' - ' + bubbletype + ' - ' + relationtype + ' - ' + str(rc) + ' rows from ' + str(offset))

        if rc == limit:
            taskqueue.Task(url='/update/relations2/%s/%s' % (bubbletype, relationtype), params={'offset': (offset + rc), 'step': (step + 1)}).add()


def main():
    Route([
            ('/update/docs', Dokumendid),
            ('/update/cache', MemCacheInfo),
            ('/update/stuff', FixStuff),
            ('/update/p2b', Person2Bubble),
            (r'/update/relations/(.*)', FixRelations),
            (r'/update/relations2/(.*)/(.*)', FixRelations2),
            (r'/update/user/(.*)', AddUser),
        ])


if __name__ == '__main__':
    main()
