from datetime import date

from bo import *
from database import *


def AggregateFeedback():
    for qanswer in db.Query(QuestionAnswer).filter('aggregation_date', date(2000, 1, 1)).fetch(100):
        aggr = Aggregation()
        aggr.type = 'feedback'
        aggr.dimensions = [
            str(qanswer.questionary.key()) + '@questionary',
            str(qanswer.course.key()) + '@course',
            str(qanswer.question.key()) + '@question',
            str(qanswer.course.key()) + '@course',
            str(qanswer.question.is_teacher_specific) + '@is_teacher_specific',
        ]
        if qanswer.question.type == 'likert' and qanswer.answer:
            aggr.sum = float(qanswer.answer)
        aggr.add()
        qanswer.aggregation_date = date.today()


def main():
    Route([
            ('/aggregate/feedback', AggregateFeedback),
        ])


if __name__ == '__main__':
    main()