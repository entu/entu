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

    def post(self):
        rc = 0
        bc = 0
        limit = 60
        step = int(self.request.get('step', 1))
        offset = int(self.request.get('offset', 0))

        bt = db.Query(Bubble).filter('path', 'message').get()
        alter = bt.GetValueAsList('notify_on_alter')

        exam_id = 5060383

        exam = Bubble().get_by_id(exam_id)

        # for g in db.Query(Bubble).filter('type', 'rating').filter('bubble', exam.key()).filter('x_is_deleted', False).order('__key__').fetch(limit=limit, offset=offset):
        #     b = Bubble().get(g.person)
            # messagetext = None

        for b in exam.GetRelatives('leecher'):
            rc += 1
            messagetext = u'Õnnitleme! Oled edukalt läbinud tootedisaini eriala esimese vooru ja oled oodatud  24. märtsil kell 10:00-16:00 Estonia pst.7-417 Disainiülesande eksamile. Kaasa võtta materjalid: joonestuspaber (3 lehte A2), lisaks paber visanditeks (A4), joonestusvahendid, värvilised pliiatsid (võivad olla ka tindipliiatsid või viltpliiatsid), käärid, liim, joonlaud, sirkel, lõikenuga ja lõikealuseks paksem kartong.'
            # if g.grade.id() == 6372319: #JAH
            #     messagetext = u'Õnnitleme. Oled edukalt läbinud stsenograafia eriala vestluse. Siit leiad sisseastumiseksamite järgmise vooru ülesanded: http://link.artun.ee/qkvfm ja http://link.artun.ee/etqwf'
            # if g.grade.id() == 6371320: #EI
            #     messagetext = u'Kahjuks sa ei läbinud stsenograafia eriala vestlust. Edu edaspidiseks.'

            if not messagetext:
                continue

            bc += 1
            # bubble = b.AddSubbubble(bt.key())
            # bubble.x_created_by = 'helen.jyrgens@artun.ee'
            # bubble.put()

            # value = bubble.SetProperty(
            #     propertykey = 'agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYk7zUAgw',
            #     oldvalue = '',
            #     newvalue = messagetext
            # )

            # message = ''
            # for t in bubble.GetProperties():
            #     message += '<b>%s</b>:<br/>\n' % t['name']
            #     message += '%s<br/>\n' % '<br/>\n'.join(['%s' % n['value'].replace('\n', '<br/>\n') for n in t['values'] if n['value']])
            #     message += '<br/>\n'

            # emails = ListMerge(getattr(b, 'email', []), getattr(b, 'user', []))
            # SendMail(
            #     to = emails,
            #     subject = Translate('message_notify_on_alter_subject') % bt.displayname.lower(),
            #     message = message,
            # )

            logging.debug(b.displayname + ' - ' + messagetext)
        logging.debug('#' + str(step) + ' - emails sent: ' + str(bc) + ' - ' + str(rc) + ' - rows from ' + str(offset))

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
                setattr(bubble, 'x_br_%s' % relationtype, ListMerge(getattr(bubble, 'x_br_%s' % relationtype, []), br.related_bubble.key()))
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
                            setattr(bubble, 'x_br_%s' % relationtype, ListMerge(getattr(bubble, 'x_br_%s' % relationtype, []), p.person2bubble))
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
        self.echo(str(db.Query(Bubble).filter('type', 'applicant').filter('x_is_deleted', False).count(limit=100000)))

    def post(self):
        rc = 0
        bc = 0
        limit = 1
        step = int(self.request.get('step', 1))
        offset = int(self.request.get('offset', 0))

        for applicant in db.Query(Bubble).filter('type', 'applicant').filter('x_is_deleted', False).order('__key__').fetch(limit=limit, offset=offset):
            rc += 1

            viewers = []
            for rh in applicant.GetValueAsList('x_br_viewer'):
                if db.get(rh).kind() == 'Bubble':
                    viewers.append(rh)
                else:
                    applicant.RemoveValue('x_br_viewer', rh)
                    applicant.put()

            viewers.append(applicant.key())

            subbubbles = applicant.GetRelatives('subbubble')

            logging.debug(str(applicant.key().id()) + ' - v:' + str(len(viewers)) + ' x sb:' + str(len(subbubbles)) + ' = r:' + str(len(viewers)*len(subbubbles)))
            for sb in subbubbles:
                sb.AddRight(viewers, 'viewer')

        logging.debug('#' + str(step) + ' - ' +str(bc) + ' - ' + str(rc) + ' rows from ' + str(offset))

        if rc == limit:
            taskqueue.Task(url='/update/applicant', params={'offset': (offset + rc), 'step': (step + 1)}).add()


class FixApplicants2(boRequestHandler):
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

        for applicant in db.Query(Bubble).filter('type', 'pre_applicant').order('__key__').fetch(limit=limit, offset=offset):
            viewers = []
            if applicant.key() not in applicant.GetValueAsList('x_br_viewer'):
                viewers.append(applicant.key())

            for submission in db.Query(Bubble).filter('type', 'submission').filter('x_br_leecher', applicant.key()).fetch(1000):
                viewers = ListMerge(viewers, submission.GetValueAsList('x_br_viewer'))

            applicant.AddRight(viewers, 'viewer')

            for sb in applicant.GetRelatives('subbubble'):
                sb.AddRight(viewers, 'viewer')

            applicant.AutoFix()


        logging.debug('#' + str(step) + ' - ' +str(bc) + ' - ' + str(rc) + ' rows from ' + str(offset))

        if rc == limit:
            taskqueue.Task(url='/update/applicant', params={'offset': (offset + rc), 'step': (step + 1)}).add()


class MarkEuro(boRequestHandler):
    def get(self):
        separator = ' : '
        # applicant_keys = Bubble().all().filter('type IN', ['applicant', 'pre_applicant'])
        # applicant_keys_str = separator.join(map(str, applicant_keys))

        euro_keys = db.Query(Bubble, keys_only = True).filter('type', 'cv_edu').filter('has_been_subsidised', True).fetch(100000)
        euro_keys_str = separator.join(map(str, euro_keys))
        identifier = '€:' + str(len(euro_keys))

        AddTask('/update/mark_euro', {
            'identifier': identifier,
            'euro_keys': euro_keys_str,
            'separator': separator,
        }, 'default')

        self.header('Content-Type', 'text/plain; charset=utf-8')
        self.echo(identifier + ' is GO')

        logging.debug(identifier + ' is GO')

    def post(self):
        separator = self.request.get('separator')
        identifier = self.request.get('identifier')
        euro_keys_str = self.request.get('euro_keys')
        euro_keys = [db.Key(r) for r in euro_keys_str.split(separator)]

        for i in range(0, 1000):
            if len(euro_keys) == 0:
                logging.debug(identifier + ': ' + 'Out of bubbles.')
                return
            euro_key = euro_keys.pop()
            b = Bubble().all().filter('x_br_subbubble', euro_key).get()
            if b:
                delattr(b, 'has_been_subsidised')
                # cv = Bubble().get(euro_key)
                # cv_str  = '"http://bubbledu.artun.ee/bubble/cv_edu#' + str(cv.key().id()) + '","'
                # cv_str += b.displayname + '","'
                # cv_str += getattr(cv,'notes','') + '","'
                # cv_str += getattr(cv,'cv_start','') + '","'
                # cv_str += getattr(cv,'cv_to','') + '","'
                # cv_str += getattr(cv,'school','') + '","'
                # cv_str += getattr(cv,'level_of_education','') + '"'
                # logging.debug(cv_str)
                # logging.debug('cv_edu ' + str(euro_key) + ' matching ' + b.displayname.encode('utf-8'))
                b.put()

        euro_keys_str = separator.join(map(str, euro_keys))
        AddTask('/update/mark_euro', {
            'identifier': identifier,
            'euro_keys': euro_keys_str,
            'separator': separator,
        }, 'default')

        logging.debug(identifier + ' - ' + str(len(euro_keys)) + 'left')


# Copy viewers to all subbubbles ( single level )
class PropagateRigths1(boRequestHandler):
    def get(self, bubble_id, right_str):
        if right_str != 'viewer':
            return 0

        self.header('Content-Type', 'text/plain; charset=utf-8')

        b = Bubble().get_by_id(int(bubble_id))
        identifier = bubble_id + ' - ' + b.displayname.encode('utf-8')
        separator = ' : '
        right_holders = []
        for rh in b.GetValueAsList('x_br_' + right_str):
            if db.get(rh).kind() == 'Bubble':
                right_holders.append(rh)
            else:
                b.RemoveValue('x_br_' + right_str, rh)
                self.echo('Encountered ' + db.get(rh).kind() + ' instead of Bubble at ' + str(rh))
                b.put()

        right_holders_str = separator.join(map(str, right_holders))

        bubble_keys = ListMerge(b.GetValueAsList('x_br_subbubble'), b.GetValueAsList('x_br_leecher'))
        bubble_keys_str = separator.join(map(str, bubble_keys))

        AddTask('/update/propagate_rights1/' + right_str + '/', {
            'right_holders': right_holders_str,
            'separator': separator,
            'bubble_keys': bubble_keys_str,
            'identifier': identifier
        }, 'default')

        logging.debug(identifier + ': ' + str(len(bubble_keys)) + ' bubbles left.')

        self.echo('Bubble ' + bubble_id + ' propagate ' + right_str + ' rights is GO')

    def post(self, right_str, bubble_key = None):
        separator = self.request.get('separator')
        identifier = self.request.get('identifier')

        right_holders_str = self.request.get('right_holders', '')
        right_holders = [db.Key(r) for r in right_holders_str.split(separator)]

        bubble_keys_str = self.request.get('bubble_keys', '')
        # bubbles = [db.Key(r) for r in bubble_keys_str.split(separator)]
        bubble_keys = bubble_keys_str.split(separator)
        for i in range(0, 10):
            if len(bubble_keys) == 0:
                logging.debug(identifier + ': ' + 'Out of bubbles.')
                return
            bubble_key = bubble_keys.pop()
            b = Bubble().get(bubble_key)
            try:
                b.AddRight(right_holders, right_str)
            except Exception, e:
                logging.debug(str(e))

        logging.debug(identifier + ': ' + str(len(bubble_keys)) + ' bubbles left.')
        bubble_keys_str = separator.join(bubble_keys)
        AddTask('/update/propagate_rights1/' + right_str + '/', {
            'right_holders': right_holders_str,
            'separator': separator,
            'bubble_keys': bubble_keys_str,
            'identifier': identifier
        }, 'default')


class PropagateRigths(boRequestHandler):
    def get(self, bubble_id, right_str):
        if right_str != 'viewer':
            return 0

        self.header('Content-Type', 'text/plain; charset=utf-8')

        b = Bubble().get_by_id(int(bubble_id))
        identifier = bubble_id + ' - ' + b.displayname.encode('utf-8')
        separator = ' : '
        right_holders = []
        for rh in b.GetValueAsList('x_br_' + right_str):
            if db.get(rh).kind() == 'Bubble':
                right_holders.append(rh)
            else:
                b.RemoveValue('x_br_' + right_str, rh)
                self.echo('Encountered ' + db.get(rh).kind() + ' instead of Bubble at ' + str(rh))
                b.put()

        right_holders_str = separator.join(map(str, right_holders))

        AddTask('/update/propagate_rights/' + right_str + '/' + str(b.key()), {
            'right_holders': right_holders_str,
            'separator': separator,
            'identifier': identifier
        }, 'default')

        self.echo('Bubble ' + bubble_id + ' propagate ' + right_str + ' rights is GO')

    def post(self, right_str, bubble_key = None):
        separator = self.request.get('separator')
        right_holders_str = self.request.get('right_holders', '')
        identifier = self.request.get('identifier')
        right_holders = [db.Key(r) for r in right_holders_str.split(separator)]

        if bubble_key:
            bubble = Bubble().get(bubble_key)

            bubble_keys = self.recurse(bubble)

            logging.debug(identifier + ': ' + str(len(bubble_keys)))
            bubble_keys = list(set(bubble_keys))
            logging.debug(identifier + ': ' + str(len(bubble_keys)))
            bubble_keys_str = separator.join(map(str, bubble_keys))
            AddTask('/update/propagate_rights/' + right_str + '/', {
                'right_holders': right_holders_str,
                'separator': separator,
                'bubble_keys': bubble_keys_str,
                'identifier': identifier
            }, 'default')
            return

        bubble_keys_str = self.request.get('bubble_keys', '')
        bubble_keys = bubble_keys_str.split(separator)
        for i in range(0, 10):
            if len(bubble_keys) == 0:
                logging.debug(identifier + ': ' + 'Out of bubbles.')
                return

            bubble_key = bubble_keys.pop()
            if not bubble_key:
                continue

            b = Bubble().get(bubble_key)
            if not b:
                continue

            try:
                b.AddRight(right_holders, right_str)
            except Exception, e:
                logging.debug('bubble: "' + str(b) + '"')
                raise e


        logging.debug(identifier + ': ' + str(len(bubble_keys)) + ' bubbles left.')
        bubble_keys_str = separator.join(bubble_keys)
        AddTask('/update/propagate_rights/' + right_str + '/', {
            'right_holders': right_holders_str,
            'separator': separator,
            'bubble_keys': bubble_keys_str,
            'identifier': identifier
        }, 'default')


    def recurse(self, bubble):
        # bubble = Bubble().get(bubble_key)
        keylist = ListMerge(bubble.GetValueAsList('x_br_subbubble'), bubble.GetValueAsList('x_br_leecher'))
        for key in keylist:
            b = Bubble().get(key)
            if not b:
                continue
            if b.kind() != 'Bubble':
                continue
            if b.x_is_deleted == True:
                continue
            keylist = keylist + self.recurse(b)
        return keylist


class TimeSlotList(boRequestHandler):
    def get(self, id):
        # self.header('Content-Type', 'text/plain; charset=utf-8')

        bubble = Bubble().get_by_id(int(id))
        csv = []
        csv.append([bubble.displayname.encode('utf-8')])
        subbubbles = bubble.GetRelatives('subbubble')
        for sb in sorted(subbubbles, key = attrgetter('start_datetime')):
            row = []
            display_leechers = []
            if sb.type != 'personal_time_slot':
                continue

            row.append(UtcToLocalDateTime(sb.start_datetime))
            leechers = sb.GetRelatives('leecher')
            for l in leechers:
                display_leechers.append(l.displayname.encode('utf-8'))

            row.append(', '.join(display_leechers))
            csv.append(row)


        self.echo_csv('%s' % bubble.displayname, csv)


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


class AddLeecher(boRequestHandler): # master / leecher
    def get(self, masterbubbleId, leecherId):
        leecher = Bubble().get_by_id(int(leecherId))
        masterbubble = Bubble().get_by_id(int(masterbubbleId))

        AddTask('/taskqueue/add_relation', {
            'bubble': str(masterbubble.key()),
            'related_bubble': str(leecher.key()),
            'type': 'leecher',
        }, 'bubble-one-by-one')


class Relate(boRequestHandler): # relation_type / master / relatee
    def get(self, relation_type, masterbubbleId, relatedbubbleId):
        try:
            masterbubble = Bubble().get_by_id(int(masterbubbleId))
            relatee = Bubble().get_by_id(int(relatedbubbleId))
        except Exception, e:
            self.header('Content-Type', 'text/plain; charset=utf-8')
            self.echo('relation_type / master / relatee')
            return

        AddTask('/taskqueue/add_relation', {
            'bubble': str(masterbubble.key()),
            'related_bubble': str(relatee.key()),
            'type': relation_type,
            'user': CurrentUser()._googleuser
        }, 'relate-%s' % relation_type)


class Unrelate(boRequestHandler): # relation_type / master / relatee
    def get(self, relation_type, masterbubbleId, relatedbubbleId):
        try:
            masterbubble = Bubble().get_by_id(int(masterbubbleId))
            relatee = Bubble().get_by_id(int(relatedbubbleId))
        except Exception, e:
            self.header('Content-Type', 'text/plain; charset=utf-8')
            self.echo('relation_type / master / relatee')
            return

        AddTask('/taskqueue/remove_relation', {
            'bubble': str(masterbubble.key()),
            'related_bubble': str(relatee.key()),
            'type': relation_type,
            'user': CurrentUser()._googleuser
        }, 'relate-%s' % relation_type)


class ExecuteNextinline(boRequestHandler): # source_bubble_id
    def get(self, sourcebubbleId):
        self.header('Content-Type', 'text/plain; charset=utf-8')

        sourcebubble = Bubble().get_by_id(int(sourcebubbleId))
        relation_type = 'leecher'

        for leecher in Bubble().get(sourcebubble.GetValueAsList('x_br_leecher')):
            if not leecher:
                continue

            rating = db.Query(Bubble).filter('type', 'rating').filter('bubble', sourcebubble.key()).filter('person', leecher.key()).get()
            grade = Bubble().get(rating.grade)
            if getattr(grade, 'is_positive', False):
                for targetbubble in Bubble().get(sourcebubble.GetValueAsList('x_br_nextinline')):
                    self.echo('bubble:' + targetbubble.displayname + '; related_bubble:' + leecher.displayname)
                    AddTask('/taskqueue/add_relation', {
                        'bubble': str(targetbubble.key()),
                        'related_bubble': str(leecher.key()),
                        'type': relation_type,
                        'user': CurrentUser()._googleuser
                    }, 'relate-%s' % relation_type)


class RemoveNextinline(boRequestHandler): # source_bubble_id
    def get(self, sourcebubbleId):
        self.header('Content-Type', 'text/plain; charset=utf-8')

        sourcebubble = Bubble().get_by_id(int(sourcebubbleId))
        relation_type = 'leecher'

        for leecher in Bubble().get(sourcebubble.GetValueAsList('x_br_leecher')):
            if not leecher:
                continue

            for targetbubble in Bubble().get(sourcebubble.GetValueAsList('x_br_nextinline')):
                self.echo('bubble:' + targetbubble.displayname + '; related_bubble:' + leecher.displayname)
                AddTask('/taskqueue/remove_relation', {
                    'bubble': str(targetbubble.key()),
                    'related_bubble': str(leecher.key()),
                    'type': relation_type,
                    'user': CurrentUser()._googleuser
                }, 'relate-%s' % relation_type)


class CopyBubble(boRequestHandler): # Assign Bubble as SubBubble to another Bubble
    def get(self, subbubbleId, masterbubbleId):
        subbubble = Bubble().get_by_id(int(subbubbleId))
        masterbubble = Bubble().get_by_id(int(masterbubbleId))

        # Add subbubble
        masterbubble.x_br_subbubble = ListMerge(masterbubble.GetValueAsList('x_br_subbubble'), subbubble.key())
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
            x_br_subbubble = ListSubtract(mb.GetValueAsList('x_br_subbubble'), subbubble.key())
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
        masterbubble.x_br_subbubble = ListMerge(masterbubble.GetValueAsList('x_br_subbubble'), subbubble.key())
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
            # x_br_subbubble = ListMerge(bubble.GetValueAsList('x_br_subbubble'), bubble.GetValueAsList('x_br_subbubble'))
            # if len(x_br_subbubble) > 0:
            #     bubble.x_br_subbubble = x_br_subbubble
            #     if hasattr(bubble, 'x_br_subbubble'):
            #         delattr(bubble, 'x_br_subbubble')
            #     bubble.put()
            # bt = db.Query(Bubble).filter('path', bubbletype).get()
            # bubble.x_type = bt.key()
            # bubble.put()

            bubble.AutoFix()

        logging.debug('#' + str(step) + ' - ' + str(rc) + ' rows from ' + str(offset))

        if rc == limit:
            taskqueue.Task(url='/update/autofix/%s' % bubbletype, params={'offset': (offset + rc), 'step': (step + 1)}).add()


class Person2TimeSlot(boRequestHandler):
    def get(self, exam_id):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        taskqueue.Task(url='/update/p2ts/%s' % exam_id).add()

    def post(self, exam_id):
        exam = Bubble().get_by_id(int(exam_id))

        sent_slots = []

        for leecher in  sorted(Bubble().get(exam.GetValueAsList('x_br_leecher')), key=attrgetter('displayname')):
            if db.Query(Bubble).filter('type', 'personal_time_slot').filter('x_br_leecher', leecher.key()).filter('__key__ IN', exam.GetValueAsList('x_br_subbubble')).get():
                continue

            for timeslot in sorted(Bubble().get(exam.GetValueAsList('x_br_subbubble')), key=attrgetter('start_datetime')):
                if timeslot.type == 'personal_time_slot' and len(timeslot.GetValueAsList('x_br_leecher')) == 0 and timeslot.key() not in sent_slots:
                    sent_slots.append(timeslot.key())
                    AddTask('/taskqueue/add_relation', {
                        'bubble': str(timeslot.key()),
                        'related_bubble': str(leecher.key()),
                        'type': 'leecher',
                    }, 'relate-leecher')
                    logging.debug('%s %s - %s' % (timeslot.displayname, timeslot.start_datetime, leecher.displayname ))
                    break


class Message2TimeSlotLeecher(boRequestHandler):
    def get(self, exam_id):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        taskqueue.Task(url='/update/m2tsl/%s' % exam_id).add()

    def post(self, exam_id):
        exam = Bubble().get_by_id(int(exam_id))
        exam_desc = exam.GetProperty(exam.GetType(), 'description')['values'][0]['value']

        rc = 0
        limit = 100
        step = int(self.request.get('step', 1))
        offset = int(self.request.get('offset', 0))

        bt = db.Query(Bubble).filter('path', 'message').get()

        for timeslot in sorted(Bubble().get(exam.GetValueAsList('x_br_subbubble')), key=attrgetter('start_datetime')):
            if timeslot.type != 'personal_time_slot':
                continue

            if getattr(timeslot, 'is_message_sent', False):
                logging.debug('%s %s already sent!' % (timeslot.displayname, timeslot.start_datetime))
                continue

            time = timeslot.GetProperty(timeslot.GetType(), 'start_datetime')['values'][0]['value']
            message = u'Oled kutsutud <b>%(time)s</b> <br><b>%(exam)s</b> <br>%(exam_desc)s' % {'exam': exam.displayname, 'exam_desc': exam_desc, 'time': time}

            for leecher in timeslot.GetRelatives('leecher'):

                bubble = leecher.AddSubbubble(bt.key(), {'message': StripTags(message)})
                bubble.x_created_by = 'helen.jyrgens@artun.ee'
                bubble.put()

                emails = ListMerge(getattr(leecher, 'email', []), getattr(leecher, 'user', []))
                SendMail(
                    to = emails,
                    subject = '%s' % exam.displayname,
                    message = message,
                )
            timeslot.is_message_sent = True
            timeslot.put()


class XXX(boRequestHandler):
    def get(self):
        self.header('Content-Type', 'text/plain; charset=utf-8')

        a = ['a', 'b', 'c', 'd']
        b = ['b', 'e', 'a']

        self.echo(ListMatch(a, b))
        self.echo(ListMatch(a, a))
        self.echo(ListMatch(a, 'a'))
        self.echo(ListMatch(a, ['x', 'y']))

        for b in db.Query(Bubble).order('message').fetch(1000):
            if hasattr(b, 'message'):
                b.notes = b.message
                delattr(b, 'message')
                b.put()



def main():
    Route([
            (r'/update/addleecher/(.*)/(.*)', AddLeecher),
            (r'/update/relate/(.*)/(.*)/(.*)', Relate),
            (r'/update/unrelate/(.*)/(.*)/(.*)', Unrelate),
            (r'/update/nil/(.*)', ExecuteNextinline),
            (r'/update/unil/(.*)', RemoveNextinline),
            (r'/update/copybubble/(.*)/(.*)', CopyBubble),
            (r'/update/movebubble/(.*)/(.*)', MoveBubble),
            (r'/update/propagate_rights/(.*)/(.*)', PropagateRigths),
            (r'/update/propagate_rights1/(.*)/(.*)', PropagateRigths1),
            (r'/update/timeslotlist/(.*)', TimeSlotList),
            ('/update/mark_euro', MarkEuro),
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
            (r'/update/p2ts/(.*)', Person2TimeSlot),
            (r'/update/m2tsl/(.*)', Message2TimeSlotLeecher),
        ])


if __name__ == '__main__':
    main()
