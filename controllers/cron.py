import datetime

from bo import *
from database import *
from datetime import datetime

class GenerateQuestionaryPersons(boRequestHandler):
    def get(self):
        message = ''

        currentdate = datetime.now().date()
        for course in db.Query(Course).filter('course_end_date <=', currentdate).filter('is_feedback_started', False).order('-course_end_date').fetch(100):
            for questionary in db.Query(Questionary).filter('end_date >=', course.course_end_date).fetch(1000):
                if questionary.start_date <= course.course_end_date:
                    message =  message + questionary.name.translate()
                    message =  message + ' "' + course.subject.name.translate() + '"'
                    message =  message + ' - ' + course.course_start_date.strftime('%d.%m.%y') + '-' + course.course_end_date.strftime('%d.%m.%y')
                    message =  message + ' - ' + str(course.subscribers.count()) + '\n'
                    for subscription in course.subscribers:
                        qp = QuestionaryPerson()
                        qp.person = subscription.student
                        qp.is_completed = False
                        qp.questionary = questionary
                        qp.course = course
                        qp.put()

                        #message =  message + '    ' + subscription.student.forename + ' ' + subscription.student.surname + ' (' + subscription.student.key().name() + ')\n'

                        for question in questionary.questions:
                            if question.is_teacher_specific:
                                teachers = Person().get(course.teachers)
                                for teacher in teachers:
                                    qa = QuestionAnswer()
                                    qa.questionary_person = qp
                                    qa.person = subscription.student
                                    qa.target_person = teacher
                                    qa.questionary = questionary
                                    qa.course = course
                                    qa.question = question
                                    qa.put()
                                    #self.response.out.write('        ' + question.name.translate() + ' (' + teacher.forename + ' ' + teacher.surname + ')\n')
                            else:
                                qa = QuestionAnswer()
                                qa.questionary_person = qp
                                qa.person = subscription.student
                                qa.questionary = questionary
                                qa.course = course
                                qa.question = question
                                qa.put()
                                #self.response.out.write('        ' + question.name.translate() + '\n')
                        #self.response.out.write('\n')

                    #message =  message + '\n'
            course.is_feedback_started = True
            course.put()

        if len(message) > 0:
            SendMail(
                to = 'argo.roots@artun.ee',
                subject = 'Questionary generated',
                message = message,
                html = False
            )


class Test(boRequestHandler):
    def get(self):
        message = ''
        for p in db.Query(Person).filter('general', 'A').fetch(1000):
            c = p.questionary_persons.count(limit=100000)
            if c > 0:
                message = message + p.surname + ' ' + p.forename + ': ' + str(c) + '\n'
            p.general = 'B'
            p.put()

        if len(message) > 0:
            SendMail(
                to = 'argo.roots@artun.ee',
                subject = 'Questionary persons',
                message = message,
                html = False
            )

def main():
    Route([
            ('/cron/generate_questionary', GenerateQuestionaryPersons),
            ('/cron/test', Test),
        ])


if __name__ == '__main__':
    main()