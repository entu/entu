# -*- coding: utf-8 -*-

from google.appengine.api import users
from google.appengine.api import memcache
from datetime import *
from random import shuffle
import time
import re
import urllib

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
        b1 = 0
        b2 = 0
        b3 = 0
        limit = 60
        step = int(self.request.get('step', 1))
        offset = int(self.request.get('offset', 0))

        bt = db.Query(Bubble).filter('path', 'message').get()
        alter = bt.GetValueAsList('notify_on_alter')

        exam_id = 5042226

        exam = Bubble().get_by_id(exam_id)

        # for b in exam.GetRelatives('leecher'):
        #     rc += 1
        #     messagetext = u'Oled läbinud  sisseastumiseksamite I vooru tekstiilidisaini erialale ning ootame Sind II vooru. Täpsema informatsiooni leiad siit http://link.artun.ee/rofgl'

        for g in db.Query(Bubble).filter('type', 'rating').filter('bubble', exam.key()).filter('x_is_deleted', False).order('__key__').fetch(limit=limit, offset=offset):
            rc += 1
            b = Bubble().get(g.person)
            messagetext = None

            if g.grade.id() == 6762206: #RE
                b1 += 1
                subjecttext = u'Teade Eesti Kunstiakadeemiasse vastu võtmise kohta'
                messagetext = u'Eesti Kunstiakadeemial on rõõm Teile teatada, et olete edukalt sooritanud sisseastumiseksamid bakalaureuseõppe stsenograafia õppekava riigieelarvelisele õppekohale.<br><br>2012. aasta gümnaasiumi lõpetajatel palume oma lõputunnistus ja riigieksamitunnistus esitada hiljemalt 25. juuniks 2012. Dokumendid võib üles laadida sisseastumissüsteemis oma avalduse juurde või tuua isiklikult 25. juunil 2012 Estonia pst.7- 265/266.<br>Lõplik nimekiri kinnitatakse 29. juunil 2012.<br><br>Eksamitööde tagastamine osakonnas 05.04-12.04.2012.<br><br>Õppeaasta algab 27. augustil 2012 sissejuhatava nädalaga (sissejuhatava nädala täpsema kava leiate EKA koduleheküljelt www.artun.ee augusti teisel poolel).<br>Õppeaasta avaaktus toimub 31.augustil 2012 (täpne kellaaeg ja koht täpsustatakse augusti teises pooles).<br>Auditoorne õppetöö algab 3. septembril 2012.<br><br>Üliõpilaseks registreeruma ei pea, kuid riigieelarvelisest õppekohast loobumisest palume teatada hiljemalt 22. juuliks 2012. Avalduse saab tuua EKA õppeosakonda (Estonia pst. 7, ruum 530) või saata meilile helen.jyrgens@artun.ee<br><br>Kui sissesaanud üliõpilane ei asu õppetööle mõjuva põhjuseta hiljemalt 10 päeva jooksul pärast õppetöö algust, siis ta eksmatrikuleeritakse ja vabanenud õppekohale immatrikuleeritakse pingereas järgmine kandidaat (Eesti Kunstiakadeemia õppekorralduseeskirja punkt 2.6.10.1.)<br><br>Ühiselamusse saab esitada avaldusi kodulehel www.yhikas.ee.<br><br><br>Vastuvõtt<br>6267 305<br>helen.jyrgens@artun.ee'

            if g.grade.id() == 6748194: #REV
                b2 += 1
                subjecttext = u'Teade Eesti Kunstiakadeemia vastuvõtu kohta'
                messagetext = u'Käesolevaga teatame, et sooritasite sisseastumiseksamid Eesti Kunstiakadeemia stsenograafia erialale positiivsele tulemusele, kuid ei pääsenud õppima riigieelarvelisele õppekohale.<br>Tasulisel õppekohal õppimise soov palume kinnitada hiljemalt 22. juuliks 2012, teatades sellest e-posti aadressile helen.jyrgens@artun.ee.<br>Peale 22. juulit 2012 teatatakse tasulised üliõpilased, kes on erialaosakonna poolt vastu võetud ja on kohustatud sõlmima õppeosakonnas (Estonia pst 7-530) lepingu  21.-22.08.2012.<br>Lepinguliste üliõpilaste I semestri õppeteenustasu tasumise tähtaeg on 24.08.2012.<br>2012. aasta gümnaasiumi lõpetajatel palume oma lõputunnistus ja riigieksamitunnistus esitada hiljemalt 25. juuniks 2012. Dokumendid võib üles laadida sisseastumissüsteemis oma avalduse juurde või tuua isiklikult 25. juunil 2012 Estonia pst.7- 265/266.<br><br>Õppeaasta algab 27. augustil 2012 sissejuhatava nädalaga.<br>Õppeaasta avaaktus toimub 31. augustil 2012 (täpne kellaaeg ja koht täpsustatakse augusti teises pooles).<br>Auditoorne õppetöö algab 3. septembril 2012.<br><br>Kui sissesaanud üliõpilane ei asu õppetööle mõjuva põhjuseta hiljemalt 10 päeva jooksul pärast õppetöö algust, siis ta eksmatrikuleeritakse ja vabanenud õppekohale immatrikuleeritakse pingereas järgmine kandidaat (Eesti Kunstiakadeemia õppekorralduseeskirja punkt 2.6.10.1.)<br><br>Ühiselamusse saab esitada avaldusi kodulehel www.yhikas.ee.<br><br>Eksamitööde tagastamine osakonnas 05.04-12.04.2012.<br><br><br>Vastuvõtt<br>6267 305<br>helen.jyrgens@artun.ee'

            # if g.grade.id() == 6766197: #EI
            #     b3 += 1
            #     subjecttext = u'Täname Teid kandideerimise eest Eesti Kunstiakadeemia vabade kunstide erialale'
            #     messagetext = u'Kahjuks ei läbinud Te sisseastumiseksameid edukalt.<br>Soovime edu edaspidiseks ja olete teretulnud järgmisel aastal uuesti proovima!<br>Oma tööd saate kätte vahemikus 05.-12.04.2012 eriala osakonnast.<br><br><br>Vastuvõtt<br>6267 305<br>helen.jyrgens@artun.ee'


            if not messagetext:
                continue

            bc += 1
            # bubble = b.AddSubbubble(bt.key())
            # bubble.x_created_by = 'helen.jyrgens@artun.ee'
            # bubble.put()

            # value = bubble.SetProperty(
            #     propertykey = 'agpzfmJ1YmJsZWR1cg8LEgZCdWJibGUYk7zUAgw',
            #     oldvalue = '',
            #     newvalue = messagetext if len(messagetext) <= 500 else messagetext[:500]
            # )

            # # message = ''
            # # for t in bubble.GetProperties():
            # #     message += '<b>%s</b>:<br/>\n' % t['name']
            # #     message += '%s<br/>\n' % '<br/>\n'.join(['%s' % n['value'].replace('\n', '<br/>\n') for n in t['values'] if n['value']])
            # #     message += '<br/>\n'

            # emails = ListMerge(getattr(b, 'email', []), getattr(b, 'user', []))
            # # SendMail(
            # #     to = emails,
            # #     subject = Translate('message_notify_on_alter_subject') % bt.displayname.lower(),
            # #     message = message,
            # # )

            # SendMail(
            #     to = emails,
            #     subject = subjecttext,
            #     message = messagetext,
            # )

            logging.debug(b.displayname + ' - ' + messagetext)
        logging.debug('#' + str(step) + ' - emails sent: ' + str(bc) + ' - (' + str(b1) + '/' + str(b2) + '/' + str(b3) + ') - ' + str(rc) + ' - rows from ' + str(offset))

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

        # If there were no deadline issues in get(), this block wouldn't be here
        if bubble_key:
            bubble_keys = self.recurse(Bubble().get(bubble_key))
            logging.debug(identifier + ': ' + str(len(bubble_keys)))
            bubble_keys = list(set(bubble_keys))
            logging.debug(identifier + ': ' + str(len(bubble_keys)))
            AddTask('/update/propagate_rights/' + right_str + '/', {
                'right_holders': right_holders_str,
                'separator': separator,
                'bubble_keys': separator.join(map(str, bubble_keys)),
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


class UnrelateByKey(boRequestHandler): # relation_type / master / relatee
    def get(self, relation_type, masterbubbleKey, relatedbubbleKey):
        try:
            masterbubble = Bubble().get(masterbubbleKey)
            relatee = Bubble().get(relatedbubbleKey)
        except Exception, e:
            self.header('Content-Type', 'text/plain; charset=utf-8')
            self.echo('relation_type / master / relatee')
            return

        AddTask('/taskqueue/remove_relation', {
            'bubble': masterbubbleKey,
            'related_bubble': relatedbubbleKey,
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
    def get(self, sourcebubbleId, targetbubbleId = None):
        self.header('Content-Type', 'text/plain; charset=utf-8')

        sourcebubble = Bubble().get_by_id(int(sourcebubbleId))
        relation_type = 'leecher'

        for leecher in Bubble().get(sourcebubble.GetValueAsList('x_br_leecher')):
            if not leecher:
                continue

            rating = db.Query(Bubble).filter('type', 'rating').filter('bubble', sourcebubble.key()).filter('person', leecher.key()).get()
            if rating:
                grade = Bubble().get(rating.grade)
            else:
                grade = Bubble()

            if getattr(grade, 'is_positive', False) or getattr(leecher, 'confirmed', False):
                if targetbubbleId:
                    targetbubble = Bubble().get_by_id(int(targetbubbleId))
                    self.echo('bubble:' + targetbubble.displayname + '; related_bubble:' + leecher.displayname)
                    AddTask('/taskqueue/add_relation', {
                        'bubble': str(targetbubble.key()),
                        'related_bubble': str(leecher.key()),
                        'type': relation_type,
                        'user': CurrentUser()._googleuser
                    }, 'relate-%s' % relation_type)
                else:
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
        try:
            subbubble = Bubble().get_by_id(int(subbubbleId))
            masterbubble = Bubble().get_by_id(int(masterbubbleId))
        except Exception, e:
            self.header('Content-Type', 'text/plain; charset=utf-8')
            self.echo('subbubbleId / masterbubbleId')
            return

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


class TranslateTitle(boRequestHandler):
    def get(self, bubbletype):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        taskqueue.Task(url='/update/translate_title/%s' % bubbletype).add()
        self.echo(str(db.Query(Bubble).filter('type', bubbletype).count(limit=1000000)))

    def post(self, bubbletype):
        limit = 20000
        step = int(self.request.get('step', 1))

        for bubble in db.Query(Bubble).filter('type', bubbletype).fetch(limit=limit):
            if not getattr(bubble, 'name', None):
                continue
            title = u'%s' % GetDictionaryValue(bubble.name, 'estonian')
            if not title:
                logging.warning('Skipping ' + bubble.displayname)
                continue

            bubble.title = title
            delattr(bubble, 'name')
            bubble.put()
            bubble.AutoFix()
            bubble.ResetCache()

        # if db.Query(Bubble, keys_only = True).filter('type', bubbletype).get():
        #     taskqueue.Task(url='/update/translate_title/%s' % bubbletype).add()


class Person2TimeSlot(boRequestHandler):
    def get(self, exam_id):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        taskqueue.Task(url='/update/p2ts/%s' % exam_id).add()

    def post(self, exam_id):
        exam = Bubble().get_by_id(int(exam_id))

        sent_slots = []

        leechers = Bubble().get(exam.GetValueAsList('x_br_leecher'))
        shuffle(leechers)
        for leecher in leechers:
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

        b = Bubble().get_by_id(6704417)
        delattr(b, 'files')
        b.put()

        for b in db.Query(Bubble).order('message').fetch(1000):
            if hasattr(b, 'message'):
                b.notes = b.message
                delattr(b, 'message')
                b.put()


class DeleteFile(boRequestHandler):
    def get(self, file_key=None):

        bs = blobstore.BlobInfo.get(urllib.unquote(file_key))
        if not bs:
            self.error(404)
            return

        delete_ok = True
        for datastore_properties in db.Query(Bubble).filter('type', 'bubble_property').filter('data_type', 'blobstore'):
            for bubble in db.Query(Bubble).filter(datastore_properties.data_property, bs.key()):
                if not bubble.Authorize('viewer'):
                    delete_ok = False
                    logging.debug('Cant remove blobstore from ' + bubble.displayname + ' | ' + str(bubble.key().id()))
                    continue
                logging.debug('Removing file from ' + bubble.displayname + ' | ' + str(bubble.key().id()))
                bubble.RemoveValue(datastore_properties.data_property, bs.key())
                bubble.put()
                bubble.ResetCache()

        if delete_ok:
            logging.debug('Deleting blobstore ' + file_key)
            bs.delete()


class ExportBubbletypes(boRequestHandler):
    def get(self):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        # self.echo(str(db.Query(Bubble).filter('type', 'bubble_type').count(limit=100000)))

        for btout in self.fetch():
            self.echo('INSERT INTO bubble_definition SET ' + ', '.join(btout) +
                ' ON DUPLICATE KEY UPDATE ' + ', '.join(btout) + ';')

    def fetch(self):
        for bt in db.Query(Bubble).filter('type', 'bubble_type').fetch(500):
            btout = []
            btout.append('gae_key = \'' + str(bt.key()) + '\'')
            if GetDictionaryValue(bt.GetValue('name'), 'estonian') :
                btout.append('estonian_label = \'' + GetDictionaryValue(bt.GetValue('name'), 'estonian') + '\'' )
            if GetDictionaryValue(bt.GetValue('name'), 'english') :
                btout.append('english_label = \'' + GetDictionaryValue(bt.GetValue('name'), 'english')  + '\'' )
            if GetDictionaryValue(bt.GetValue('name_plural'), 'estonian') :
                btout.append('estonian_label_plural = \'' + GetDictionaryValue(bt.GetValue('name_plural'), 'estonian') + '\'' )
            if GetDictionaryValue(bt.GetValue('name_plural'), 'english') :
                btout.append('english_label_plural = \'' + GetDictionaryValue(bt.GetValue('name_plural'), 'english')  + '\'' )
            if GetDictionaryValue(bt.GetValue('description'), 'estonian') :
                btout.append('estonian_description = \'' + GetDictionaryValue(bt.GetValue('description'), 'estonian') + '\'' )
            if GetDictionaryValue(bt.GetValue('description'), 'english') :
                btout.append('english_description = \'' + GetDictionaryValue(bt.GetValue('description'), 'english')  + '\'' )
            if bt.GetValue('property_displayname', '') :
                btout.append('estonian_displayname = \'' + bt.GetValue('property_displayname', '') + '\'' )
            if bt.GetValue('property_displayname', '') :
                btout.append('english_displayname = \'' + bt.GetValue('property_displayname', '') + '\'' )
            if bt.GetValue('property_displayinfo', '') :
                btout.append('estonian_displayinfo = \'' + bt.GetValue('property_displayinfo', '') + '\'' )
            if bt.GetValue('property_displayinfo', '') :
                btout.append('english_displayinfo = \'' + bt.GetValue('property_displayinfo', '') + '\'' )
            if bt.GetValue('property_displaytable', '') :
                btout.append('estonian_displaytable = \'' + bt.GetValue('property_displaytable', '')+ '\'' )
            if bt.GetValue('property_displaytable', '') :
                btout.append('english_displaytable = \'' + bt.GetValue('property_displaytable', '')+ '\'' )
            if bt.GetValue('sort_string', '') :
                btout.append('estonian_sort = \'' + bt.GetValue('sort_string', '') + '\'' )
            if bt.GetValue('sort_string', '') :
                btout.append('english_sort = \'' + bt.GetValue('sort_string', '') + '\'' )
            # btout['search_properties'] = bt.search_properties
            yield btout


class ExportBubbletype(boRequestHandler):
    def get(self, bubbletype_path = None):
        self.header('Content-Type', 'text/plain; charset=utf-8')

        # To avoid "Exceeded soft private memory limit with 528.277 MB after servicing 1 requests total" we limit the number of bubbles in one run
        chunk_size = 500 #1000 looks viable for most bubbles

        if not bubbletype_path:
            bubbletype_paths = ['course','earticle','inventory_computer','institution','award_grant','applicant_doc','document','submission','exam','personal_time_slot','exam_group','rating_scale','grade_on_scale','inventory','folder','cv_edu','doc_kirjavahetus','classifier','cl_value','conference_presentation','cv_edu_ba','cv_edu_ma','creative_activity','doc_lahetuskorraldus','emedia','module','bubble_type','doc_other','department','person','doc_publication','epublication','book','library','state_exam','bubble_configuration','semester','applicant','pre_applicant','phd_applicant','rating','bubble_relation_template','concentration','message','event','timetable','cv_work','doc_vastuskiri','reception','reception_group','bubble_property','study_group','curriculum','subject','level_of_education']
            self.echo('Initialaizing tasks for all bubble types:\n' + str(bubbletype_paths))
            for bubbletype_path in bubbletype_paths:
                post_url = '/update/export/bubbletype/%s' % bubbletype_path
                AddTask(post_url, [], 'default', 'GET')

            self.echo('<hr/>\nDon\'t forget to run these before import:')
            self.echo('INSERT IGNORE INTO bubble_definition (gae_key, created, created_by, changed, changed_by, deleted, deleted_by, allowed_subtypes_id, estonian_label, estonian_label_plural, estonian_description, estonian_displayname, estonian_displayinfo, estonian_displaytable, estonian_sort, english_label, english_label_plural, english_description, english_displayname, english_displayinfo, english_displaytable, english_sort) VALUES (\'classifier\', NULL, NULL, NULL, NULL, NULL, NULL, NULL, \'Klassifikaator\', \'Klassifikaatorid\', NULL, \'@name@\', NULL, NULL, \'@name@\', \'Classifier\', \'Classifiers\', NULL, \'@name@\', NULL, NULL, \'@name@\');')
            self.echo('INSERT IGNORE INTO bubble_definition (gae_key, created, created_by, changed, changed_by, deleted, deleted_by, allowed_subtypes_id, estonian_label, estonian_label_plural, estonian_description, estonian_displayname, estonian_displayinfo, estonian_displaytable, estonian_sort, english_label, english_label_plural, english_description, english_displayname, english_displayinfo, english_displaytable, english_sort) VALUES (\'classifier value\', NULL, NULL, NULL, NULL, NULL, NULL, NULL, \'Klassifikaatori väärtus\', \'Klassifikaatori väärtused\', NULL, \'@name@\', NULL, NULL, \'@name@\', \'Classifier Value\', \'Classifier Values\', NULL, \'@name@\', NULL, NULL, \'@name@\');')
            self.echo('INSERT IGNORE INTO property_definition (gae_key, created, created_by, changed, changed_by, deleted, deleted_by, bubble_definition_id, dataproperty, estonian_fieldset, estonian_label, estonian_label_plural, estonian_description, estonian_formatstring, english_fieldset, english_label, english_label_plural, english_description, english_formatstring, datatype, defaultvalue, ordinal, multiplicity, readonly, createonly, public, mandatory, search, propagates, autocomplete, classifying_bubble_definition_id, target_property_definition_id) VALUES (\'classifier name\', NULL, NULL, NULL, NULL, NULL, NULL, (SELECT id FROM bubble_definition WHERE gae_key=\'classifier\'), \'name\', NULL, \'Nimi\', \'Nimed\', NULL, NULL, NULL, \'Name\', \'Names\', NULL, NULL, \'dictionary\', NULL, 3, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0);')
            self.echo('INSERT IGNORE INTO property_definition (gae_key, created, created_by, changed, changed_by, deleted, deleted_by, bubble_definition_id, dataproperty, estonian_fieldset, estonian_label, estonian_label_plural, estonian_description, estonian_formatstring, english_fieldset, english_label, english_label_plural, english_description, english_formatstring, datatype, defaultvalue, ordinal, multiplicity, readonly, createonly, public, mandatory, search, propagates, autocomplete, classifying_bubble_definition_id, target_property_definition_id) VALUES (\'classifier value name\', NULL, NULL, NULL, NULL, NULL, NULL, (SELECT id FROM bubble_definition WHERE gae_key=\'classifier value\'), \'name\', NULL, \'Nimi\', \'Nimed\', NULL, NULL, NULL, \'Name\', \'Names\', NULL, NULL, \'dictionary\', NULL, 3, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0);')
            return

        bubbletype = db.Query(Bubble).filter('path', bubbletype_path).get()
        properties = {}
        for bprop_key in bubbletype.GetValueAsList('bubble_properties'): #  bubbletype.bubble_properties:
            bprop = Bubble().get(bprop_key)

            if bprop.data_type not in properties:
                properties[bprop.data_type] = bprop.data_property
            else:
                properties[bprop.data_type] = properties[bprop.data_type] + ',' + bprop.data_property


        self.echo(str(db.Query(Bubble).filter('type', bubbletype_path).count(limit=1000000)))

        post_url = '/update/export/bubbletype/%s' % bubbletype_path

        post_data = properties
        post_data['post_property_types'] = ','.join(properties.keys())
        self.echo(post_data['post_property_types'])

        post_bubble_keys = map(str, db.Query(Bubble, keys_only = True).filter('type', bubbletype_path).fetch(1000000))

        for key_chunk in self.chunks(post_bubble_keys, chunk_size):
            post_data['post_bubble_keys'] = ','.join(key_chunk)
            try:
                AddTask(post_url, post_data, 'default')
            except Exception, e:
                logging.debug('Failed to request ' + '/update/export/bubbletype/%s' % bubbletype_path)
                raise e

    def chunks(self, l, n):
        for i in xrange(0, len(l), n):
            yield l[i:i+n]


    def post(self, bubbletype_path):
        post_property_types = self.request.get('post_property_types').split(',')
        post_bubble_keys = self.request.get('post_bubble_keys').split(',')

        bubbletype = db.Query(Bubble).filter('path', bubbletype_path).get()
        bt_key = str(bubbletype.key())
        property_keys = {}
        for bprop_key in bubbletype.GetValueAsList('bubble_properties'):
            bprop = Bubble().get(bprop_key)
            property_keys[bprop.data_property] = str(bprop_key)

        b_sql = []

        for b_key in post_bubble_keys:
            if b_key == '':
                continue

            b_out = []
            b_out.append(u'gae_key = \'%s\'' % b_key)
            b_out.append(u'bubble_definition_id = (SELECT id FROM bubble_definition WHERE gae_key = \'%s\')' % bt_key )

            try:
                bubble = Bubble().get(b_key)
            except Exception, e:
                logging.debug('b_key = "%s"' % str(b_key))
                raise e

            if getattr(bubble, 'is_public', False):
                b_out.append(u'public = 1')

            if getattr(bubble, 'x_is_deleted', False):
                b_out.append(u'deleted = 1')

            x_changed = bubble.GetValue('x_changed')
            if x_changed:
                b_out.append(u'changed = \'%s\'' % str(x_changed)[:19])

            x_changed_by = bubble.GetValue('x_changed_by')
            if x_changed_by:
                b_out.append(u'changed_by = \'%s\'' % x_changed_by )

            x_created = bubble.GetValue('x_created')
            if x_created:
                b_out.append(u'created = \'%s\'' % str(x_created)[:19])

            x_created_by = bubble.GetValue('x_created_by')
            if x_created_by:
                b_out.append(u'created_by = \'%s\'' % x_created_by)

            join_out = u', '.join(b_out)
            b_sql.append(u'INSERT INTO bubble SET %s ON DUPLICATE KEY UPDATE %s;' % (join_out, join_out))

            #####
            # continue
            #####

            b_fk = u'bubble_id = (SELECT id FROM bubble WHERE gae_key = \'%s\')' % b_key
            b_sql.append(u'DELETE FROM property WHERE %s;' % b_fk)

            # post_property_types: string,reference,blobstore,dictionary_select,boolean,date,select
            value_type = {
                'string':            u'value_string',
                'text':              u'value_text',
                'dictionary_string': u'value_string',
                'dictionary_text':   u'value_text',
                'integer':           u'value_integer',
                'float':             u'value_decimal',
                'date':              u'value_datetime',
                'datetime':          u'value_datetime',
                'reference':         u'value_reference',
                'blobstore':         u'value_file',
                'boolean':           u'value_boolean',
                'select':            u'value_select',
                'dictionary_select': u'value_select',
                'counter':           u'value_counter',
                }
            for post_property_type in post_property_types:
                post_property_names = self.request.get(post_property_type)
                # logging.debug(post_property_type + ': ' + post_property_names)
                post_property_type_value = value_type[post_property_type]

                for post_property_name in post_property_names.split(','):
                    pd_key = bt_key + '_' + property_keys[post_property_name]
                    pd_fk = u'property_definition_id = (SELECT id FROM property_definition WHERE gae_key = \'%s\')' % pd_key

                    if post_property_type in ['string', 'text', 'select']:
                        for b_value in bubble.GetValueAsList(post_property_name):
                            if b_value:
                                b_out = [b_fk]
                                b_out.append(pd_fk)
                                try:
                                    foo = b_value.replace('\'', '\\\'')
                                except AttributeError, e:
                                    foo = str(b_value)
                                b_out.append(u'%s = \'%s\'' % (post_property_type_value, foo))
                                b_sql.append(u'INSERT INTO property SET %s ON DUPLICATE KEY UPDATE %s;' % (u', '.join(b_out), u', '.join(b_out)))

                    elif post_property_type in ['dictionary_string', 'dictionary_text']:
                        for b_value in bubble.GetValueAsList(post_property_name):

                            b_value_estonian = GetDictionaryValue(b_value, 'estonian')
                            if b_value_estonian:
                                b_out = [b_fk]
                                b_out.append(pd_fk)
                                b_out.append(u'language = \'estonian\'')
                                try:
                                    foo = b_value_estonian.replace('\'', '\\\'')
                                except AttributeError, e:
                                    foo = str(b_value_estonian)
                                b_out.append(u'%s = \'%s\'' % (post_property_type_value, foo))
                                b_sql.append(u'INSERT INTO property SET %s ON DUPLICATE KEY UPDATE %s;' % (u', '.join(b_out), u', '.join(b_out)))

                            b_value_english = GetDictionaryValue(b_value, 'english')
                            if b_value_english:
                                b_out = [b_fk]
                                b_out.append(pd_fk)
                                b_out.append(u'language = \'english\'')
                                try:
                                    foo = b_value_english.replace('\'', '\\\'')
                                except AttributeError, e:
                                    foo = str(b_value_english)
                                b_out.append(u'%s = \'%s\'' % (post_property_type_value, foo))
                                b_sql.append(u'INSERT INTO property SET %s ON DUPLICATE KEY UPDATE %s;' % (u', '.join(b_out), u', '.join(b_out)))

                    elif post_property_type in ['dictionary_select']:
                        for value_gae_key in bubble.GetValueAsList(post_property_name):
                            classifier_gae_key = GetDictionaryName(value_gae_key)

                            # Bubble for classifier
                            classifier_bubbledefinition_fk = u'bubble_definition_id = (SELECT id FROM bubble_definition WHERE gae_key = \'classifier\')'

                            b_out = [classifier_bubbledefinition_fk]
                            b_out.append(u'gae_key = \'%s\'' % classifier_gae_key)
                            b_sql.append(u'INSERT INTO bubble SET %s ON DUPLICATE KEY UPDATE %s;' % (u', '.join(b_out), u', '.join(b_out)))

                            # Properties for classifier name
                            classifier_bubble_fk = u'bubble_id = (SELECT id FROM bubble WHERE gae_key = \'%s\')' % classifier_gae_key
                            b_sql.append(u'DELETE FROM property WHERE %s;' % classifier_bubble_fk)

                            classifier_name_propertydefinition_fk = u'property_definition_id = (SELECT id FROM property_definition WHERE gae_key = \'classifier name\')'

                            b_out = [classifier_name_propertydefinition_fk]
                            b_out.append(classifier_bubble_fk)
                            b_out.append(u'language = \'estonian\'')
                            b_out.append(u'value_string = \'%s\'' % classifier_gae_key)
                            b_sql.append(u'INSERT INTO property SET %s;' % u', '.join(b_out))

                            b_out = [classifier_name_propertydefinition_fk]
                            b_out.append(classifier_bubble_fk)
                            b_out.append(u'language = \'english\'')
                            b_out.append(u'value_string = \'%s\'' % classifier_gae_key)
                            b_sql.append(u'INSERT INTO property SET %s;' % u', '.join(b_out))

                            # Bubble for classifier value
                            classifier_value_bubbledefinition_fk = u'bubble_definition_id = (SELECT id FROM bubble_definition WHERE gae_key = \'classifier value\')'

                            b_out = [classifier_value_bubbledefinition_fk]
                            b_out.append(u'gae_key = \'%s\'' % value_gae_key)
                            b_sql.append(u'INSERT INTO bubble SET %s ON DUPLICATE KEY UPDATE %s;' % (u', '.join(b_out), u', '.join(b_out)))

                            # Properties for classifier value name and store value properties of bubble
                            # Instead of reference(s) to selected classifier value(s) we'll store string values
                            clvalue_bubble_fk = u'bubble_id = (SELECT id FROM bubble WHERE gae_key = \'%s\')' % value_gae_key
                            b_sql.append(u'DELETE FROM property WHERE %s;' % clvalue_bubble_fk)

                            clv_name_propertydefinition_fk = u'property_definition_id = (SELECT id FROM property_definition WHERE gae_key = \'classifier value name\')'

                            b_value_estonian = GetDictionaryValue(value_gae_key, 'estonian').replace('\'', '\\\'')
                            if b_value_estonian:
                                b_out = [clv_name_propertydefinition_fk]    # property for classifier
                                b_out.append(clvalue_bubble_fk)
                                b_out.append(u'language = \'estonian\'')
                                b_out.append(u'value_string = \'%s\'' % b_value_estonian)
                                b_sql.append(u'INSERT INTO property SET %s;' % u', '.join(b_out))

                                b_out = [b_fk]                              # property for bubble
                                b_out.append(pd_fk)
                                b_out.append(u'language = \'estonian\'')
                                b_out.append(u'%s = \'%s\'' % (post_property_type_value, b_value_estonian))
                                b_sql.append(u'INSERT INTO property SET %s ON DUPLICATE KEY UPDATE %s;' % (u', '.join(b_out), u', '.join(b_out)))

                            b_value_english = GetDictionaryValue(value_gae_key, 'english').replace('\'', '\\\'')
                            if b_value_english:
                                b_out = [clv_name_propertydefinition_fk]    # property for classifier
                                b_out.append(clvalue_bubble_fk)
                                b_out.append(u'language = \'english\'')
                                b_out.append(u'value_string = \'%s\'' % b_value_english)
                                b_sql.append(u'INSERT INTO property SET %s;' % u', '.join(b_out))

                                b_out = [b_fk]                              # property for bubble
                                b_out.append(pd_fk)
                                b_out.append(u'language = \'english\'')
                                b_out.append(u'%s = \'%s\'' % (post_property_type_value, b_value_english))
                                b_sql.append(u'INSERT INTO property SET %s ON DUPLICATE KEY UPDATE %s;' % (u', '.join(b_out), u', '.join(b_out)))



                    elif post_property_type in ['integer','float']:
                        for b_value in bubble.GetValueAsList(post_property_name):
                            if b_value:
                                b_out = [b_fk]
                                b_out.append(pd_fk)
                                b_out.append(u'%s = \'%s\'' % (post_property_type_value, str(b_value)))
                                b_sql.append(u'INSERT INTO property SET %s ON DUPLICATE KEY UPDATE %s;' % (u', '.join(b_out), u', '.join(b_out)))

                    elif post_property_type in ['date', 'datetime']:
                        for b_value in bubble.GetValueAsList(post_property_name):
                            if b_value:
                                b_out = [b_fk]
                                b_out.append(pd_fk)
                                b_out.append(u'%s = \'%s\'' % (post_property_type_value, str(b_value)[:19]))
                                b_sql.append(u'INSERT INTO property SET %s ON DUPLICATE KEY UPDATE %s;' % (u', '.join(b_out), u', '.join(b_out)))

                    elif post_property_type == 'reference':
                        for b_value in bubble.GetValueAsList(post_property_name):
                            if b_value:
                                b_out = [b_fk]
                                b_out.append(pd_fk)
                                b_out.append(u'%s = (SELECT id FROM bubble WHERE gae_key = \'%s\')' % (post_property_type_value, str(b_value)))
                                b_sql.append(u'INSERT INTO property SET %s ON DUPLICATE KEY UPDATE %s;' % (u', '.join(b_out), u', '.join(b_out)))

                    elif post_property_type == 'blobstore':
                        for b_value in bubble.GetValueAsList(post_property_name):
                            if b_value:
                                blobfile = blobstore.BlobInfo.get(b_value)
                                created = str(blobfile.creation)[:19]
                                filesize = blobfile.size
                                filename = blobstore.BlobInfo.get(b_value).filename.replace('\'', '\\\'')
                                gae_key = str(b_value)
                                b_sql.append(u'INSERT INTO file SET gae_key=\'%s\', filename=\'%s\', filesize=%s, created=\'%s\' ON DUPLICATE KEY UPDATE gae_key=\'%s\', filename=\'%s\', filesize=%s, created=\'%s\';' % (gae_key, filename, str(filesize), created, gae_key, filename, str(filesize), created))

                                b_out = [b_fk]
                                b_out.append(pd_fk)
                                b_out.append(u'%s = (SELECT id FROM file WHERE gae_key = \'%s\')' % (post_property_type_value, str(b_value)))
                                b_sql.append(u'INSERT INTO property SET %s ON DUPLICATE KEY UPDATE %s;' % (u', '.join(b_out), u', '.join(b_out)))

                    elif post_property_type == 'boolean':
                        b_value = bubble.GetValue(post_property_name, False)
                        if b_value:
                            b_out = [b_fk]
                            b_out.append(pd_fk)
                            b_out.append(u'%s = 1' % post_property_type_value)
                            b_sql.append(u'INSERT INTO property SET %s ON DUPLICATE KEY UPDATE %s;' % (u', '.join(b_out), u', '.join(b_out)))

                    else:
                        continue

        SendMail(
            to = ['mihkel.putrinsh@artun.ee'],#, 'argo.roots@artun.ee'],
            subject = 'bubbles for ' + bubbletype_path,
            message = bubbletype_path,
            attachments = [('bubbles_' + bubbletype_path + '.sql', u'\n'.join(b_sql))]
        )

        return 0


class ExportR2D2(boRequestHandler):
    def get(self):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        self.echo(str(db.Query(Bubble).filter('type', 'bubble_property').count(limit=100000)))

        post_url = '/update/export/r2d2'
        post_data = []
        try:
            AddTask(post_url, post_data, 'default')
        except Exception, e:
            logging.debug('Failed to request ' + post_url)
            raise e

    def post(self):
        b_sql = []
        for bt in db.Query(Bubble).filter('type', 'bubble_type').fetch(100000):
            for propkey in bt.GetValueAsList('bubble_properties'):
                btlist = []
                btlist.append('gae_key = \'' + str(bt.key()) + '_' + str(propkey) + '\'')

                bubble_property = Bubble().get(propkey)

                label_estonian = GetDictionaryValue(bubble_property.GetValue('name'), 'estonian')
                if label_estonian:
                    btlist.append('estonian_label = \'' + label_estonian.replace('\'', '\\\'') + '\'' )
                label_english = GetDictionaryValue(bubble_property.GetValue('name'), 'english')
                if label_english:
                    btlist.append('english_label = \'' + label_english.replace('\'', '\\\'') + '\'' )

                label_estonian_plural = GetDictionaryValue(bubble_property.GetValue('name_plural'), 'estonian')
                if label_estonian_plural:
                    btlist.append('estonian_label_plural = \'' + label_estonian_plural.replace('\'', '\\\'') + '\'' )
                label_english_plural = GetDictionaryValue(bubble_property.GetValue('name_plural'), 'english')
                if label_english_plural:
                    btlist.append('english_label_plural = \'' + label_english_plural.replace('\'', '\\\'') + '\'' )

                description_estonian = GetDictionaryValue(bubble_property.GetValue('description'), 'estonian')
                if description_estonian:
                    btlist.append('estonian_description = \'' + description_estonian.replace('\'', '\\\'') + '\'' )
                description_english = GetDictionaryValue(bubble_property.GetValue('description'), 'english')
                if description_english:
                    btlist.append('english_description = \'' + description_english.replace('\'', '\\\'') + '\'' )

                target_property_str = bubble_property.GetValue('target_property')
                if target_property_str:
                    property_key = str(db.Query(Bubble, keys_only=True).filter('type', 'bubble_property').filter('data_property', target_property_str).get())
                    btlist.append('target_property_definition_id = (SELECT id FROM property_definition WHERE gae_key = \'' + property_key + '\')')

                field_group_estonian = GetDictionaryValue(bubble_property.GetValue('field_group'), 'estonian')
                if field_group_estonian:
                    btlist.append('estonian_fieldset = \'' + field_group_estonian.replace('\'', '\\\'') + '\'' )
                field_group_english = GetDictionaryValue(bubble_property.GetValue('field_group'), 'english')
                if field_group_english:
                    btlist.append('english_fieldset = \'' + field_group_english.replace('\'', '\\\'') + '\'' )

                data_type = bubble_property.GetValue('data_type')
                if data_type:
                    btlist.append('datatype = \'' + data_type.replace('\'', '\\\'') + '\'' )
                data_property = bubble_property.GetValue('data_property')
                if data_property:
                    btlist.append('dataproperty = \'' + data_property.replace('\'', '\\\'') + '\'' )
                format_string = bubble_property.GetValue('format_string')
                if format_string:
                    btlist.append('estonian_formatstring = \'' + format_string.replace('\'', '\\\'') + '\'' )
                    btlist.append('english_formatstring = \'' + format_string.replace('\'', '\\\'') + '\'' )
                default = bubble_property.GetValue('default')
                if default:
                    btlist.append('defaultvalue = \'' + default.replace('\'', '\\\'') + '\'' )

                ordinal = bubble_property.GetValue('ordinal')
                if ordinal:
                    btlist.append('ordinal = ' + str(ordinal) + '' )
                count = bubble_property.GetValue('count')
                if count:
                    btlist.append('multiplicity = ' + str(count) + '' )

                is_auto_complete = bubble_property.GetValue('is_auto_complete')
                if is_auto_complete:
                    btlist.append('autocomplete = 1')

                btlist.append('bubble_definition_id = (SELECT id FROM bubble_definition WHERE gae_key = \'' + str(bt.key()) + '\')')
                if propkey in bt.GetValueAsList('mandatory_properties'):
                    btlist.append('mandatory = 1')
                if propkey in bt.GetValueAsList('public_properties'):
                    btlist.append('public = 1')
                if propkey in bt.GetValueAsList('search_properties'):
                    btlist.append('search = 1')
                if propkey in bt.GetValueAsList('create_only_properties'):
                    btlist.append('createonly = 1')
                if propkey in bt.GetValueAsList('read_only_properties'):
                    btlist.append('readonly = 1')
                if propkey in bt.GetValueAsList('propagated_properties'):
                    btlist.append('propagates = 1')

                b_sql.append(u'INSERT INTO property_definition SET ' + u', '.join(btlist) + ' ON DUPLICATE KEY UPDATE ' + u', '.join(btlist) + ';\n')

        SendMail(
            to = ['mihkel.putrinsh@artun.ee'],#, 'argo.roots@artun.ee'],
            subject = 'bubbles for ' + 'r2d2',
            message = 'r2d2',
            attachments = [('r2d2.sql', '\n'.join(b_sql))]
        )


def main():
    Route([
            (r'/update/addleecher/(.*)/(.*)', AddLeecher),
            (r'/update/relate/(.*)/(.*)/(.*)', Relate),
            (r'/update/unrelate/(.*)/(.*)/(.*)', Unrelate),
            (r'/update/unrelate_by_key/(.*)/(.*)/(.*)', UnrelateByKey),
            (r'/update/nil/(.*)/(.*)', ExecuteNextinline),
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
            (r'/update/translate_title/(.*)', TranslateTitle),
            (r'/update/relations/(.*)', FixRelations),
            (r'/update/relations2/(.*)/(.*)', FixRelations2),
            (r'/update/relations3/(.*)/(.*)', FixRelations3),
            (r'/update/type/(.*)', FixType),
            (r'/update/type2(.*)/(.*)', ChangeBubbleType),
            (r'/update/p2ts/(.*)', Person2TimeSlot),
            (r'/update/m2tsl/(.*)', Message2TimeSlotLeecher),
            (r'/update/delete_file/(.*)', DeleteFile),
            ('/update/export/bubbletypes', ExportBubbletypes),
            (r'/update/export/bubbletype/(.*)', ExportBubbletype),
            ('/update/export/r2d2', ExportR2D2),
        ])


if __name__ == '__main__':
    main()
