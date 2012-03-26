from datetime import *

from bo import *
from database.bubble import *
from database.dictionary import *


class TimeSlot(boRequestHandler):
    def get(self, bubble_id):
        bubble = Bubble().get_by_id(int(bubble_id))
        if not bubble.Authorize('viewer'):
            self.error(404)
            return

        self.view(
            main_template = '',
            template_file = 'action/timeslot.html',
            values = {
                'bubble': bubble,
            }
        )

    def post(self, bubble_id):
        AddTask('/taskqueue/action_timeslot/%s' % bubble_id, {
            'start': self.request.get('start').strip(),
            'end': self.request.get('end').strip(),
            'interval': self.request.get('interval').strip(),
            'user': CurrentUser()._googleuser
        }, 'one-by-one')


class Rating(boRequestHandler):
    def get(self, bubble_id):
        bubble = Bubble().get_by_id(int(bubble_id))
        if not bubble.Authorize('viewer'):
            self.error(404)
            return

        is_print = self.request.get('print').strip().lower() == 'true'

        ratingscale = Bubble().get(bubble.rating_scale)

        grades = {}
        for g in ratingscale.GetRelatives('subbubble'):
            grades[str(g.key())] = {
                'key': str(g.key()),
                'displayname' : g.displayname,
                'sort': getattr(g, 'x_sort_%s' % UserPreferences().current.language),
                'is_positive': getattr(g, 'is_positive', False),
                'equivalent': getattr(g, 'equivalent', 0),
            }

        ratings = {}
        for r in bubble.GetRelatives('subbubble', 'rating'):
            if r.x_is_deleted == False and getattr(r, 'grade', False):
                ratings[str(r.person)] = grades[str(r.grade)]

        leechers = {}
        for l in bubble.GetRelatives('leecher'):
            leechers[str(l.key())] = {
                'key': str(l.key()),
                'displayname' : l.displayname,
                'grade': ratings[str(l.key())] if str(l.key()) in ratings else False,
                'equivalent' : 0
            }

        subgrades = {}
        allgrades = {}
        subbubbles = {}
        for s in bubble.GetRelatives('subbubble', 'exam'):
            subbubbles[str(s.key())] = {
                'displayname': s.displayname,
            }


            for sr in s.GetRelatives('subbubble', 'rating'):
                if str(sr.person) not in leechers or  sr.x_is_deleted == True or not getattr(sr, 'grade', False):
                    continue
                if str(sr.grade) not in allgrades:
                    gb = Bubble().get(sr.grade)
                    allgrades[str(sr.grade)] = {
                        'displayname': gb.displayname,
                        'is_positive': getattr(gb, 'is_positive', False),
                        'equivalent': getattr(gb, 'equivalent', 0),
                    }

                leechers[str(sr.person)]['equivalent'] += allgrades[str(sr.grade)]['equivalent']
                subgrades[str(sr.bubble)+str(sr.person)] = {'grade': allgrades[str(sr.grade)], 'bubble': subbubbles[str(s.key())]}

        for bk, bv in subbubbles.iteritems():
            for lk, lv in leechers.iteritems():
                if 'subgrades' not in lv:
                    leechers[lk]['subgrades'] = []
                if bk+lk in subgrades:
                    leechers[lk]['subgrades'].append(subgrades[bk+lk])
                else:
                    leechers[lk]['subgrades'].append('X')

        if is_print:
            leechers = sorted(leechers.values(), key=itemgetter('equivalent'), reverse=True)
        else:
            leechers = sorted(leechers.values(), key=itemgetter('displayname'))

        self.view(
            main_template = 'main/print.html' if is_print else '',
            template_file =  'action/rating_print.html' if is_print else 'action/rating.html',
            values = {
                'bubble': bubble,
                'grades': sorted(grades.values(), key=itemgetter('sort')),
                'subbubbles': subbubbles.values(),
                'leechers': leechers,
            }
        )

    def post(self, bubble_id):
        bubble = Bubble().get_by_id(int(bubble_id))
        person = Bubble().get(self.request.get('person').strip())
        if self.request.get('grade').strip():
            grade_key = db.Key(self.request.get('grade').strip())

            bt = db.Query(Bubble).filter('type', 'bubble_type').filter('path', 'rating').get()
            rating = db.Query(Bubble).filter('type', 'rating').filter('person', person.key()).filter('bubble', bubble.key()).get()
            if not rating:
                rating = person.AddSubbubble(bt.key(), {'grade': grade_key, 'person': person.key(), 'bubble': bubble.key()})
            else:
                rating.grade = grade_key
                rating.x_is_deleted = False
                rating.put()

            AddTask('/taskqueue/add_relation', {
                'bubble': str(bubble.key()),
                'related_bubble': str(rating.key()),
                'type': 'subbubble',
                'user': CurrentUser()._googleuser
            }, 'relate-subbubble')
        else:
            rating = db.Query(Bubble).filter('type', 'rating').filter('person', person.key()).filter('bubble', bubble.key()).get()
            if rating:
                rating.x_is_deleted = True
                rating.put()

                AddTask('/taskqueue/remove_relation', {
                    'bubble': str(bubble.key()),
                    'related_bubble': str(rating.key()),
                    'type': 'subbubble',
                    'user': CurrentUser()._googleuser
                }, 'relate-subbubble')

                AddTask('/taskqueue/remove_relation', {
                    'bubble': str(person.key()),
                    'related_bubble': str(rating.key()),
                    'type': 'subbubble',
                    'user': CurrentUser()._googleuser
                }, 'relate-subbubble')



def main():
    Route([
            (r'/action/timeslot/(.*)', TimeSlot),
            (r'/action/rating/(.*)', Rating),
        ])


if __name__ == '__main__':
    main()
