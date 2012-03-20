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
        grades = sorted(ratingscale.GetRelatives('subbubble'), key=attrgetter('x_sort_%s' % UserPreferences().current.language))
        leechers = sorted(bubble.GetRelatives('leecher'), key=attrgetter('displayname'))
        ratings = {}
        for r in bubble.GetRelatives('subbubble', 'rating'):
            ratings[str(r.person)] = r.grade

        for l in leechers:
            if str(l.key()) in ratings:
                l.grade = ratings[str(l.key())]

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
        grade_key = db.Key(self.request.get('grade').strip())

        newbubble = db.Query(Bubble).filter('type', 'rating').filter('person', person.key()).filter('bubble', bubble.key()).get()
        if not newbubble:
            newbubble = person.AddSubbubble(rating.key(), {'grade': grade_key, 'person': person.key(), 'bubble': bubble.key()})
        else:
            newbubble.grade = grade_key
            newbubble.put()

        AddTask('/taskqueue/add_relation', {
            'bubble': str(bubble.key()),
            'related_bubble': str(newbubble.key()),
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
