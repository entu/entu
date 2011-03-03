from datetime import date

from bo import *
from database import *


class AggregateFeedback(boRequestHandler):
    def get(self):
        for qperson in db.Query(QuestionaryPerson).filter('aggregation_date', date(2000, 1, 1)).filter('is_completed', True).filter('is_obsolete', False).fetch(50):
            for qanswer in qperson.answers:
                aggr = Aggregation()

                aggr.dimensions = [
                    str(qanswer.question.key()) + '@question',
                    str(qanswer.course.key()) + '@course',
                    str(qanswer.person.key()) + '@person',
                ]
                if qanswer.target_person:
                    aggr.dimensions.append(str(qanswer.target_person.key()) + '@target_person')
                else:
                    aggr.dimensions.append('none@target_person')

                aggr.defining_dimensions = [
                    'feedback',
                    str(qanswer.questionary.key()) + '@questionary',
                    str(qanswer.question.is_teacher_specific) + '@is_teacher_specific',
                ]

                if qanswer.question.type == 'text':
                    aggr.text_value = qanswer.answer
                else:
                    if qanswer.answer:
                        aggr.float_value = float(qanswer.answer)
                aggr.add()

            qperson.aggregation_date = date.today()
            qperson.put()
        self.response.out.write('OK')


def main():
    Route([
            ('/aggregate/feedback', AggregateFeedback),
        ])


if __name__ == '__main__':
    main()