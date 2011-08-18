from google.appengine.api import taskqueue

import string
from datetime import *
from operator import attrgetter

from bo import *
from database.bubble import *
from database.person import *
from database.dictionary import *


class ShowRating(boRequestHandler):
    def get(self, bubble_id):
        if not self.authorize('bubbler'):
            return # TODO: give a proper error page or something

        bubble_id = bubble_id.strip('/')
        if not bubble_id:
            return # TODO: give a proper error page or something

        bubble = Bubble().get_by_id(int(bubble_id))
        if not bubble:
            return # TODO: give a proper error page or something

        rateable_sub_bubbles = bubble.RateableSubBubbles
        if rateable_sub_bubbles:
            rateable_sub_bubbles = sorted(rateable_sub_bubbles, key=attrgetter('sortdate'))
        ratingscale = bubble.rating_scale
        gradedefinitions = sorted(ratingscale.GradeDefinitions, key=attrgetter('equivalent'), reverse=True)
        subgrades = sorted(bubble.SubGrades, key=lambda k: k.bubble.sortdate)

        leechers = sorted(bubble.Leechers, key=lambda k: k.key(), reverse=True)
        grades = sorted(bubble.Grades, key=lambda k: k.person.key(), reverse=True)

        for leecher in leechers:
            leecher.equivalent = 0
            leecher.grade_key = None
            leecher.grade_equivalent = 999999
            leecher.grade_displayname = Translate('bubble_not_rated')
            leecher.grade_is_locked = False
            for grade in grades:
                if grade.person.key() == leecher.key():
                    gd = grade.gradedefinition
                    leecher.grade_key = gd.key()
                    leecher.grade_equivalent = gd.equivalent
                    leecher.grade_displayname = gd.displayname
                    leecher.grade_is_locked = grade.is_locked
                    break

            leecher.subgrades = []
            for subgrade in subgrades:
                if subgrade.person.key() == leecher.key():
                    leecher.subgrades.append(subgrade)
                    if subgrade.equivalent:
                        leecher.equivalent += subgrade.equivalent

        self.view('application', 'rating/rating.html', {
            'bubble': bubble,
            'leechers': leechers,
            'ratingscale': ratingscale,
            'gradedefinitions': gradedefinitions,
            'gradebubbles': rateable_sub_bubbles
        })

    def post(self, bubble_id):
        if self.authorize('bubbler'):
            bubble_id = bubble_id.strip('/')
            person_key = self.request.get('person').strip()
            gradedefinition_key = self.request.get('grade').strip()

            if bubble_id:
                bubble = Bubble().get_by_id(int(bubble_id))

                if gradedefinition_key:
                    gradedefinition = GradeDefinition().get(gradedefinition_key)
                else:
                    gradedefinition = None

                grade = db.Query(Grade).filter('person', db.Key(person_key)).filter('bubble', bubble).get()
                if not grade:
                    grade = Grade()
                    grade.person = db.Key(person_key)
                    grade.bubble = bubble
                grade.bubble_type = bubble.type
                grade.datetime = datetime.now()
                #grade.name =
                grade.points = bubble.points
                #grade.school =
                #grade.teacher =
                #grade.teacher_name =
                if gradedefinition:
                    grade.gradedefinition = gradedefinition
                    grade.equivalent = gradedefinition.equivalent
                    grade.is_positive = gradedefinition.is_positive
                    grade.is_deleted = False
                else:
                    grade.is_deleted = True
                grade.put()


class LockRating(boRequestHandler):
    def get(self, bubble_id):
        if self.authorize('bubbler'):
            bubble_id = bubble_id.strip('/')
            if bubble_id:
                bubble = Bubble.get_by_id(int(bubble_id))

                for g in db.Query(Grade).filter('is_deleted', False).filter('is_locked', False).filter('bubble', bubble.key()).fetch(1000):
                #for g in db.Query(Grade).filter('is_deleted', False).filter('bubble', bubble.key()).fetch(1000):
                    if g.person.key() in bubble.leechers:
                        g.is_locked = True
                        g.put()

                        if g.is_positive == True:
                            taskqueue.Task(url='/taskqueue/bubble_pass_leechers', params={'bubble_key': str(g.bubble.key()), 'person_key': str(g.person.key())}).add(queue_name='one-by-one')

                self.redirect('/rating/' + bubble_id)


def main():
    Route([
            (r'/rating/lock/(.*)', LockRating),
            (r'/rating/(.*)', ShowRating),
        ])


if __name__ == '__main__':
    main()