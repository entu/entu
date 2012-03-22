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

        ratingscale = Bubble().get(bubble.rating_scale)

        grades = []
        for g in ratingscale.GetRelatives('subbubble'):
            grades.append({
                'key': str(g.key()),
                'displayname' : g.displayname,
                'sort': 'x_sort_%s' % UserPreferences().current.language
            })
        grades = sorted(grades, key=itemgetter('sort'))

        ratings = {}
        for r in bubble.GetRelatives('subbubble', 'rating'):
            if r.x_is_deleted == False and getattr(r, 'grade', False):
                ratings[str(r.person)] = str(r.grade)

        leechers = []
        for l in bubble.GetRelatives('leecher'):
            leechers.append({
                'key': str(l.key()),
                'displayname' : l.displayname,
                'grade': ratings[str(l.key())] if str(l.key()) in ratings else False
            })
        leechers = sorted(leechers, key=itemgetter('displayname'))

        self.view(
            main_template = '',
            template_file = 'action/rating.html',
            values = {
                'bubble': bubble,
                'grades': grades,
                'leechers': leechers,
            }
        )

    def post(self, bubble_id):
        bubble = Bubble().get_by_id(int(bubble_id))
        person = Bubble().get(self.request.get('person').strip())
        rating = db.Query(Bubble).filter('type', 'bubble_type').filter('path', 'rating').get()
        if self.request.get('grade').strip():
            grade_key = db.Key(self.request.get('grade').strip())

            rating = db.Query(Bubble).filter('type', 'rating').filter('person', person.key()).filter('bubble', bubble.key()).get()
            if not rating:
                rating = person.AddSubbubble(rating.key(), {'grade': grade_key, 'person': person.key(), 'bubble': bubble.key()})
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
