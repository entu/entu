# -*- coding: utf-8 -*-

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


class SendMessage(boRequestHandler):
    def get(self):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        taskqueue.Task(url='/update/sendmessage').add()
        self.echo(str(db.Query(Bubble).filter('type', 'pre_applicant').filter('x_is_deleted', False).count(limit=100000)))

    def post(self):
        rc = 0
        limit = 100
        step = int(self.request.get('step', 1))
        offset = int(self.request.get('offset', 0))

        bt = db.Query(Bubble).filter('path', 'message').get()
        alter = bt.GetValueAsList('notify_on_alter')

        for b in db.Query(Bubble).filter('type', 'pre_applicant').filter('x_is_deleted', False).order('__key__').fetch(limit=limit, offset=offset):
            rc += 1

            # bubble = b.AddSubbubble(bt.key())
            # bubble.x_created_by = 'helen.jyrgens@artun.ee'
            # bubble.put()

            # value = bubble.SetProperty(
            #     propertykey = 'agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYk7zUAgw',
            #     oldvalue = '',
            #     newvalue = u'Kandideerimiseks Eesti Kunstiakadeemiasse täida avaldus lõpuni ja vajuta avalduse lõpus olevat nuppu "Esita avaldus"'
            # )

            # message = ''
            # for t in bubble.GetProperties():
            #     message += '<b>%s</b>:<br/>\n' % t['name']
            #     message += '%s<br/>\n' % '<br/>\n'.join(['%s' % n['value'].replace('\n', '<br/>\n') for n in t['values'] if n['value']])
            #     message += '<br/>\n'

            # emails = MergeLists(getattr(b, 'email', []), getattr(b, 'user', []))
            # SendMail(
            #     to = emails,
            #     subject = Translate('message_notify_on_alter_subject') % bt.displayname.lower(),
            #     message = message,
            # )

        logging.debug('#' + str(step) + ' - ' + str(rc) + ' rows from ' + str(offset))

        if rc == limit:
            taskqueue.Task(url='/update/sendmessage', params={'offset': (offset + rc), 'step': (step + 1)}).add()


class FixRelations(boRequestHandler): # BubbleRelation to Bubble.x_br_...
    def get(self, relationtype=None):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        # for r in ['subbubble','seeder','leecher','editor','owner','subbubbler','viewer']:
        for r in ['leecher']:
            # taskqueue.Task(url='/update/relations/%s' % r).add()
            self.echo(r + ': ' + str(db.Query(BubbleRelation).filter('type', r).filter('x_is_deleted', False).count(limit=100000)))

    def post(self, relationtype):
        rc = 0
        limit = 500
        step = int(self.request.get('step', 1))
        offset = int(self.request.get('offset', 0))

        for br in db.Query(BubbleRelation).filter('type', relationtype).filter('x_is_deleted', False).order('__key__').fetch(limit=limit, offset=offset):
            rc += 1
            try:
                bubble = br.bubble
                setattr(bubble, 'x_br_%s' % relationtype, MergeLists(getattr(bubble, 'x_br_%s' % relationtype, []), br.related_bubble.key()))
                bubble.put()
            except:
                pass
        logging.debug('#' + str(step) + ' - ' + relationtype + ' - ' + str(rc) + ' rows from ' + str(offset))

        if rc == limit:
            taskqueue.Task(url='/update/relations/%s' % relationtype, params={'offset': (offset + rc), 'step': (step + 1)}).add()


class FixRelations2(boRequestHandler): # Change Person keys from Bubble.x_br_... to Bubble keys
    def get(self, bubbletype, relationtype=None):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        for r in ['subbubble','seeder','leecher','editor','owner','subbubbler','viewer']:
            taskqueue.Task(url='/update/relations2/%s/%s' % (bubbletype, r)).add()
        self.echo(str(db.Query(Bubble).filter('type', bubbletype).filter('x_is_deleted', False).count(limit=100000)))

    def post(self, bubbletype, relationtype):
        rc = 0
        limit = 10
        step = int(self.request.get('step', 1))
        offset = int(self.request.get('offset', 0))

        for bubble in db.Query(Bubble).filter('type', bubbletype).order('__key__').fetch(limit=limit, offset=offset):
            rc += 1
            for r in bubble.GetValueAsList('x_br_%s' % relationtype):
                p = db.get(r)
                if p:
                    if p.kind() == 'Person':
                        if hasattr(p, 'person2bubble'):
                            setattr(bubble, 'x_br_%s' % relationtype, MergeLists(getattr(bubble, 'x_br_%s' % relationtype, []), p.person2bubble))
                            bubble.put()

        logging.debug('#' + str(step) + ' - ' + bubbletype + ' - ' + relationtype + ' - ' + str(rc) + ' rows from ' + str(offset))

        if rc == limit:
            taskqueue.Task(url='/update/relations2/%s/%s' % (bubbletype, relationtype), params={'offset': (offset + rc), 'step': (step + 1)}).add()
        else:
            taskqueue.Task(url='/update/relations3/%s/x' % bubbletype, method='GET').add()


class FixRelations3(boRequestHandler): # Bubble.x_br_... to Bubblerelation
    def get(self, bubbletype, relationtype=None):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        for r in ['subbubble','seeder','leecher','editor','owner','subbubbler','viewer']:
            taskqueue.Task(url='/update/relations3/%s/%s' % (bubbletype, r)).add()
        self.echo(str(db.Query(Bubble).filter('type', bubbletype).filter('x_is_deleted', False).count(limit=100000)))

    def post(self, bubbletype, relationtype):
        rc = 0
        limit = 10
        step = int(self.request.get('step', 1))
        offset = int(self.request.get('offset', 0))

        for bubble in db.Query(Bubble).filter('type', bubbletype).order('__key__').fetch(limit=limit, offset=offset):
            rc += 1
            for r in bubble.GetValueAsList('x_br_%s' % relationtype):
                p = db.get(r)
                if p:
                    if p.kind() == 'Bubble':
                        br = db.Query(BubbleRelation).filter('bubble', bubble.key()).filter('related_bubble', p.key()).filter('type', relationtype).get()
                        if not br:
                            br = BubbleRelation()
                            br.bubble = bubble.key()
                            br.related_bubble = p.key()
                        br.type = relationtype
                        br.x_is_deleted = False
                        br.put()

        logging.debug('#' + str(step) + ' - ' + bubbletype + ' - ' + relationtype + ' - ' + str(rc) + ' rows from ' + str(offset))

        if rc == limit:
            taskqueue.Task(url='/update/relations3/%s/%s' % (bubbletype, relationtype), params={'offset': (offset + rc), 'step': (step + 1)}).add()


class FixType(boRequestHandler):
    def get(self, bubbletype):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        taskqueue.Task(url='/update/type/%s' % bubbletype).add()
        self.echo(str(db.Query(Bubble).filter('type', bubbletype).filter('x_is_deleted', False).count(limit=100000)))

    def post(self, bubbletype):
        rc = 0
        limit = 200
        step = int(self.request.get('step', 1))
        offset = int(self.request.get('offset', 0))

        for bubble in db.Query(Bubble).filter('type', bubbletype).order('__key__').fetch(limit=limit, offset=offset):
            rc += 1
            if not hasattr(bubble, 'x_type'):
                bt = db.Query(Bubble).filter('type', 'bubble_type').filter('path', bubble.type).get()
                setattr(bubble, 'x_type', bt.key())
                bubble.put()

        logging.debug('#' + str(step) + ' - ' + bubbletype + ' - ' + str(rc) + ' rows from ' + str(offset))

        if rc == limit:
            taskqueue.Task(url='/update/type/%s' % bubbletype, params={'offset': (offset + rc), 'step': (step + 1)}).add()


class FixApplicants(boRequestHandler):
    def get(self):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        taskqueue.Task(url='/update/applicant').add()
        self.echo(str(db.Query(Bubble).filter('type', 'pre_applicant').filter('x_is_deleted', False).count(limit=100000)))

    def post(self):
        rc = 0
        bc = 0
        limit = 200
        step = int(self.request.get('step', 1))
        offset = int(self.request.get('offset', 0))

        for bubble in db.Query(Bubble).filter('type', 'pre_applicant').order('__key__').fetch(limit=limit, offset=offset):
            rc += 1
            bubble.AutoFix()
            # if len(bubble.GetValueAsList('x_br_viewer')) < 2 or not getattr(bubble, 'forename', None) or not getattr(bubble, 'surname', None):
            #     bt = db.Query(Bubble).filter('type', 'bubble_type').filter('path', 'pre_applicant').get()
            #     bubble.type = bt.path
            #     bubble.x_type = bt.key()
            #     bubble.put()
            #     bc += 1

        logging.debug('#' + str(step) + ' - ' +str(bc) + ' - ' + str(rc) + ' rows from ' + str(offset))

        if rc == limit:
            taskqueue.Task(url='/update/applicant', params={'offset': (offset + rc), 'step': (step + 1)}).add()


class ChangeBubbleType(boRequestHandler):
    def get(self, type, id):
        self.header('Content-Type', 'text/plain; charset=utf-8')

        bt = db.Query(Bubble).filter('path', type).get()
        if not bt:
            self.echo('No %s!' % type)
            return

        b = Bubble().get_by_id(int(id))
        if not b:
            self.echo('No %s!' % id)
            return

        self.echo(b.type + ' -> ' + bt.path)
        b.x_type = bt.key()
        b.type = bt.path
        b.put()
        b.AutoFix()


class AddLeecher(boRequestHandler):
    def get(self, leecherId, masterbubbleId):
        leecher = Bubble().get_by_id(int(leecherId))
        masterbubble = Bubble().get_by_id(int(masterbubbleId))

        AddTask('/taskqueue/add_relation', {
            'bubble': str(masterbubble.key()),
            'related_bubble': str(leecher.key()),
            'type': 'leecher',
        }, 'bubble-one-by-one')


class CopyBubble(boRequestHandler): # Assign Bubble as SubBubble to another Bubble
    def get(self, subbubbleId, masterbubbleId):
        subbubble = Bubble().get_by_id(int(subbubbleId))
        masterbubble = Bubble().get_by_id(int(masterbubbleId))

        # Add subbubble
        masterbubble.x_br_subbubble = MergeLists(masterbubble.GetValueAsList('x_br_subbubble'), subbubble.key())
        masterbubble.put()

        # Create BubbleRelation's
        br = db.Query(BubbleRelation).filter('bubble', masterbubble.key()).filter('related_bubble', subbubble.key()).filter('type', 'subbubble').get()
        if not br:
            br = BubbleRelation()
            br.bubble = masterbubble.key()
            br.related_bubble = subbubble.key()
            br.type = 'subbubble'
            br.put()
        else:
            if br.x_is_deleted != False:
                br.x_is_deleted = False
                br.put()


class MoveBubble(boRequestHandler): # Assign Bubble as SubBubble to another Bubble
    def get(self, subbubbleId, masterbubbleId):
        subbubble = Bubble().get_by_id(int(subbubbleId))
        masterbubble = Bubble().get_by_id(int(masterbubbleId))

        # Remove from all previous master bubbles
        for mb in db.Query(Bubble).filter('x_br_subbubble', subbubble.key()).fetch(1000):
            x_br_subbubble = RemoveFromList(subbubble.key(), mb.GetValueAsList('x_br_subbubble'))
            if len(x_br_subbubble) > 0:
                mb.x_br_subbubble = x_br_subbubble
            else:
                delattr(mb, 'x_br_subbubble')
            mb.put()

        # Remove all previous BubbleRelations
        for br in db.Query(BubbleRelation).filter('related_bubble', subbubble.key()).filter('type', 'subbubble').filter('x_is_deleted', False).fetch(1000):
            br.x_is_deleted = True
            br.put()

        # Add subbubble
        masterbubble.x_br_subbubble = MergeLists(masterbubble.GetValueAsList('x_br_subbubble'), subbubble.key())
        masterbubble.put()

        # Create BubbleRelation
        br = db.Query(BubbleRelation).filter('bubble', masterbubble.key()).filter('related_bubble', subbubble.key()).filter('type', 'subbubble').get()
        if not br:
            br = BubbleRelation()
            br.bubble = masterbubble.key()
            br.related_bubble = subbubble.key()
            br.type = 'subbubble'
            br.put()
        else:
            if br.x_is_deleted != False:
                br.x_is_deleted = False
                br.put()


class AutoFixBubble(boRequestHandler):
    def get(self, bubbletype):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        taskqueue.Task(url='/update/autofix/%s' % bubbletype).add()
        self.echo(str(db.Query(Bubble).filter('type', bubbletype).count(limit=1000000)))

    def post(self, bubbletype):
        rc = 0
        limit = 20
        step = int(self.request.get('step', 1))
        offset = int(self.request.get('offset', 0))

        for bubble in db.Query(Bubble).filter('type', bubbletype).order('__key__').fetch(limit=limit, offset=offset):
            rc += 1
            # x_br_subbubble = MergeLists(bubble.GetValueAsList('x_br_subbuble'), bubble.GetValueAsList('x_br_subbubble'))
            # if len(x_br_subbubble) > 0:
            #     bubble.x_br_subbubble = x_br_subbubble
            #     if hasattr(bubble, 'x_br_subbuble'):
            #         delattr(bubble, 'x_br_subbuble')
            #     bubble.put()
            # bt = db.Query(Bubble).filter('path', bubbletype).get()
            # bubble.x_type = bt.key()
            # bubble.put()

            if bubble.type in ['applicant', 'pre_applicant']:
                if bubble.key() not in bubble.GetValueAsList('x_br_viewer'):
                    AddTask('/taskqueue/rights', {
                        'bubble': str(bubble.key()),
                        'person': str(bubble.key()),
                        'right': 'viewer',
                    }, 'bubble-one-by-one')

                for br in db.Query(BubbleRelation).filter('x_is_deleted', False).filter('related_bubble', bubble.key()).filter('type', 'leecher').fetch(100):
                    b = br.bubble
                    if getattr(b, 'type', '') == 'submission':
                        for p in b.GetValueAsList('x_br_viewer'):
                            AddTask('/taskqueue/rights', {
                                'bubble': str(bubble.key()),
                                'person': str(p),
                                'right': 'viewer',
                            }, 'bubble-one-by-one')

                        for sb in bubble.GetRelatives('subbubble'):
                            for p in sb.GetValueAsList('x_br_viewer'):
                                AddTask('/taskqueue/rights', {
                                    'bubble': str(bubble.key()),
                                    'person': str(p),
                                    'right': 'viewer',
                                }, 'bubble-one-by-one')
                            sb.put()

            bubble.AutoFix()

        logging.debug('#' + str(step) + ' - ' + str(rc) + ' rows from ' + str(offset))

        if rc == limit:
            taskqueue.Task(url='/update/autofix/%s' % bubbletype, params={'offset': (offset + rc), 'step': (step + 1)}).add()


class XXX(boRequestHandler):
    def get(self):
        self.header('Content-Type', 'text/plain; charset=utf-8')

        a = sorted(['a', 'd', 'c', 'b'])
        b = sorted(['a', 'b', 'c', 'd'])

        self.echo(a==b)

        # for bubble in db.Query(BubbleRelation).filter('type', 'subbuble').fetch(100):
        #     br = db.Query(BubbleRelation).filter('bubble', bubble.bubble).filter('related_bubble', bubble.related_bubble).filter('type', 'subbubble').get()
        #     if br:
        #         bubble.delete()
        #         self.echo('a'+str(bubble.key().id()))
        #     else:
        #         bubble.type = 'subbubble'
        #         bubble.put()
        #         self.echo('b'+str(bubble.key().id()))



def main():
    Route([
            (r'/update/addleecher/(.*)/(.*)', AddLeecher),
            (r'/update/copybubble/(.*)/(.*)', CopyBubble),
            (r'/update/movebubble/(.*)/(.*)', MoveBubble),
            ('/update/applicant', FixApplicants),
            ('/update/cache', MemCacheInfo),
            ('/update/docs', Dokumendid),
            ('/update/xxx', XXX),
            ('/update/sendmessage', SendMessage),
            (r'/update/autofix/(.*)', AutoFixBubble),
            (r'/update/relations/(.*)', FixRelations),
            (r'/update/relations2/(.*)/(.*)', FixRelations2),
            (r'/update/relations3/(.*)/(.*)', FixRelations3),
            (r'/update/type/(.*)', FixType),
            (r'/update/type2(.*)/(.*)', ChangeBubbleType),
        ])


if __name__ == '__main__':
    main()
