import datetime

from bo import *
from database import *
from datetime import datetime

class ShowQuestionariesList(webapp.RequestHandler):
    def get(self):
        q = db.Query(Questionary).order('-start_date').fetch(1000)
        View(self, 'questionary', 'questionary_list.html', {
            'questionaries': q,
        })


class ShowQuestionary(webapp.RequestHandler):
    def get(self, key):
        if key:
            questionary = db.get(key)
        else:
            questionary = None

        View(self, 'questionary', 'questionary.html', {
            'questionary': questionary,
        })

    def post(self, key):
        name = self.request.get('name').strip()
        start_date = self.request.get('start_date').strip()
        end_date = self.request.get('end_date').strip()
        description = self.request.get('description').strip()

        if key:
            q = db.get(key)
        else:
            q = Questionary()
        q.name = DictionaryAdd('questionary_name', name)
        if start_date:
            q.start_date = datetime.strptime(start_date, '%d.%m.%Y').date()
        if end_date:
            q.end_date = datetime.strptime(end_date, '%d.%m.%Y').date()
        q.description = DictionaryAdd('questionary_description', description)
        q.put()

        if not key:
            self.response.out.write(str(q.key()))



class DeleteQuestionary(webapp.RequestHandler):
    def get(self, key):
        for q in db.Query(Question).filter('questionary', db.Key(key)).fetch(1000):
            q.delete()

        q = db.Query(Questionary).filter('__key__', db.Key(key)).get()
        q.delete()
        self.redirect('/questionary')


class EditQuestion(webapp.RequestHandler):
    def post(self):
        questionary_key = self.request.get('questionary').strip()
        name = self.request.get('name').strip()
        type = self.request.get('type').strip()
        mandatory = self.request.get('mandatory').strip()
        teacher_specific = self.request.get('teacher_specific').strip()

        q = Question()
        q.questionary = db.Key(questionary_key)
        q.name = DictionaryAdd('question_name', name)
        q.type = type
        if mandatory:
            q.is_mandatory = True
        if teacher_specific:
            q.is_teacher_specific = True
        q.put()

        self.redirect('/questionary/' + questionary_key)


class DeleteQuestion(webapp.RequestHandler):
    def get(self, key):
        q = db.Query(Question).filter('__key__', db.Key(key)).get()
        q.delete()


class GenerateQuestionaryPersons(webapp.RequestHandler):
    def get(self):

        self.response.headers['Content-Type'] = 'text/plain; charset=UTF-8'

        currentdate = datetime.now().date()
        #for course in db.Query(Course).filter('course_end_date <=', currentdate).filter('is_feedback_started', False).order('-course_end_date').fetch(1000):
        for course in db.Query(Course).filter('__key__', db.Key('agdib25nYXBwchcLEgZDb3Vyc2UiC2NvdXJzZV84MzYxDA')).fetch(1000):
            for questionary in db.Query(Questionary).filter('end_date >=', course.course_end_date).fetch(1000):
                if questionary.start_date <= course.course_end_date:
                    self.response.out.write(questionary.name.translate() + ':\n')
                    for subscription in course.subscribers:
                        qp = QuestionaryPerson()
                        qp.person = subscription.student
                        qp.is_completed = False
                        qp.questionary = questionary
                        qp.course = course
                        qp.put()

                        self.response.out.write('    ' + subscription.student.forename + ' ' + subscription.student.surname + ':\n')

                        for question in questionary.questions:
                            if question.is_teacher_specific:
                                teachers = Person().get(course.teachers)
                                for teacher in teachers:
                                    qa = QuestionAnswer()
                                    qa.question = question
                                    qa.questionary_person = qp
                                    qa.teacher = teacher
                                    qa.put()
                                    self.response.out.write('        ' + question.name.translate() + ' (' + teacher.forename + ' ' + teacher.surname + ')\n')
                            else:
                                qa = QuestionAnswer()
                                qa.question = question
                                qa.questionary_person = qp
                                qa.is_mandatory = question.is_mandatory
                                qa.put()
                                self.response.out.write('        ' + question.name.translate() + '\n')
                        self.response.out.write('\n')

                    self.response.out.write('\n\n')
            course.is_feedback_started = True
            course.put()


def main():
    Route([
            ('/questionary', ShowQuestionariesList),
            ('/questionary/generate', GenerateQuestionaryPersons),
            ('/questionary/delete/(.*)', DeleteQuestionary),
            ('/questionary/question/delete/(.*)', DeleteQuestion),
            ('/questionary/question', EditQuestion),
            ('/questionary/(.*)', ShowQuestionary)
        ])


if __name__ == '__main__':
    main()