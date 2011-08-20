import datetime
from datetime import datetime

from bo import *
from database.person import *
from database.bubble import *
from database.aggregation import *
from database.zimport.zoin import *


class SyncBubbleSeeders(boRequestHandler):
    def get(self):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        for b in db.Query(Bubble).filter('type', 'submission').fetch(10000):
            p = db.Query(Person, keys_only=True).filter('seeder', b).fetch(10000)
            if p != b.seeders:
                b.seeders=p
                b.put()
                self.echo(str(b.key()) + ' - ' + str(p) + '\n')


class SyncBubbleLeechers(boRequestHandler):
    def get(self):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        for b in db.Query(Bubble).filter('type', 'submission').fetch(10000):
            p = db.Query(Person, keys_only=True).filter('leecher', b).fetch(10000)
            if p != b.leechers:
                b.leechers=p
                b.put()
                self.echo(str(b.key()) + ' - ' + str(p) + '\n')


class DeleteAggregation(boRequestHandler):
    def get(self):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        for b in db.Query(AggregationValue).fetch(3000):
            b.delete()







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
        for p in db.Query(Person).filter('model_version', 'B').fetch(500):
            if not db.Query(Zoin).filter('new_key', str(p.key())).get():
                message = message + str(p.key()) + '\n'
            else:
                p.model_version = 'C'
                p.put()

        if len(message) > 0:
            SendMail(
                to = 'argo.roots@artun.ee',
                subject = 'Double persons',
                message = message,
                html = False
            )


def main():
    Route([
            ('/cron/sync_bubble_seeders', SyncBubbleSeeders),
            ('/cron/sync_bubble_leechers', SyncBubbleLeechers),
            ('/cron/delete_aggregation', DeleteAggregation),
            ('/cron/generate_questionary', GenerateQuestionaryPersons),
            ('/cron/test', Test),
        ])


if __name__ == '__main__':
    main()