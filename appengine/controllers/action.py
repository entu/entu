# -*- coding: utf-8 -*-

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

        # Collect all possible grades on scale
        grades = {}
        for g in ratingscale.GetRelatives('subbubble'):
            grades[str(g.key())] = {
                'key': str(g.key()),
                'displayname' : g.displayname,
                'sort': getattr(g, 'x_sort_%s' % UserPreferences().current.language),
                'is_positive': getattr(g, 'is_positive', False),
                'equivalent': getattr(g, 'equivalent', 0),
            }

        # Collect all ratings that match available grades
        ratings = {}
        for r in bubble.GetRelatives('subbubble', 'rating'):
            if r.x_is_deleted == False and getattr(r, 'grade', False) and str(r.grade) in grades:
                ratings[str(r.person)] = grades[str(r.grade)]

        # Collect leechers of bubble
        leechers = {}
        for l in bubble.GetRelatives('leecher'):
            leechers[str(l.key())] = {
                'key': str(l.key()),
                'displayname' : l.displayname,
                'grade': ratings[str(l.key())] if str(l.key()) in ratings else False,
                'equivalent' : 0,
                'is_positive' : ratings[str(l.key())]['is_positive'] if str(l.key()) in ratings else False,
                'ordinal' : 9999999,
            }

        subgrades = {}
        allgrades = {}
        exams = {}
        for exam_bubble in bubble.GetRelatives('subbubble', 'exam'):
            exam_key = str(exam_bubble.key())
            exams[exam_key] = {
                'displayname': exam_bubble.displayname,
            }

            for exam_rating in exam_bubble.GetRelatives('subbubble', 'rating'):
                if exam_rating.x_is_deleted == True:
                    continue
                if str(exam_rating.person) not in leechers:
                    logging.warning('Person ' + str(exam_rating.person) + ' not in leechers of bubble ' + str(bubble.key()))
                    continue
                if not getattr(exam_rating, 'grade', False):
                    logging.warning('Rating ' + str(exam_rating.key()) + ' has no grade')
                    continue
                grade_key = str(exam_rating.grade)
                if grade_key not in allgrades:
                    grade_bubble = Bubble().get(exam_rating.grade)
                    allgrades[grade_key] = {
                        'displayname': grade_bubble.displayname,
                        'is_positive': getattr(grade_bubble, 'is_positive', False),
                        'equivalent': getattr(grade_bubble, 'equivalent', 0),
                    }

                leechers[str(exam_rating.person)]['equivalent'] += allgrades[grade_key]['equivalent']
                leechers[str(exam_rating.person)]['ordinal'] -= getattr(exam_rating, 'ordinal', 0)
                leechers[str(exam_rating.person)]['is_positive'] = False if allgrades[grade_key]['is_positive'] == False else leechers[str(exam_rating.person)]['is_positive']
                subgrades[str(exam_rating.bubble)+str(exam_rating.person)] = {'grade': allgrades[grade_key], 'bubble': exams[exam_key]}

        for bk, bv in exams.iteritems():
            for lk, lv in leechers.iteritems():
                if 'subgrades' not in lv:
                    leechers[lk]['subgrades'] = []
                if bk+lk in subgrades:
                    leechers[lk]['subgrades'].append(subgrades[bk+lk])
                else:
                    leechers[lk]['subgrades'].append('X')

        #logging.debug('Leechers:' + str(leechers))
        if is_print:
            leechers = sorted(leechers.values(), key=itemgetter('is_positive', 'equivalent', 'ordinal'), reverse=True)
        else:
            leechers = sorted(leechers.values(), key=itemgetter('displayname', 'ordinal'))

        self.view(
            main_template = 'main/print.html' if is_print else '',
            template_file =  'action/rating_print.html' if is_print else 'action/rating.html',
            values = {
                'bubble': bubble,
                'grades': sorted(grades.values(), key=itemgetter('sort')),
                'subbubbles': exams.values(),
                'leechers': leechers,
                'print_private_ratings': True,
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


class SendPrivateRatingList(boRequestHandler):
    def get(self, bubble_id):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        taskqueue.Task(url='/taskqueue/private_rating_list/%s' % bubble_id).add()
        bubble = Bubble().get_by_id(int(bubble_id))
        self.echo(u'%s - pingeread käivitatud.' % bubble.displayname)


def main():
    Route([
            (r'/action/timeslot/(.*)', TimeSlot),
            (r'/action/rating/(.*)', Rating),
            (r'/action/private_rating_list/(.*)', SendPrivateRatingList),
        ])


if __name__ == '__main__':
    main()
