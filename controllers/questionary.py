import datetime

from bo import *
from database import *
from datetime import datetime

class ShowQuestionariesList(boRequestHandler):
    def get(self):
        if self.authorize('questionary'):
            q = db.Query(Questionary).order('-start_date').fetch(1000)
            self.view('questionary', 'questionary_list.html', {
                'questionaries': q,
            })


class ShowQuestionary(boRequestHandler):
    def get(self, key):
        if self.authorize('questionary'):
            if key:
                questionary = db.get(key)
            else:
                questionary = None

            self.view('questionary', 'questionary.html', {
                'questionary': questionary,
            })

    def post(self, key):
        if self.authorize('questionary'):
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


class ShowQuestionaryResults(boRequestHandler):
    def get(self, key):
        if self.authorize('questionary'):
            pass


class SortQuestionary(boRequestHandler):
    def post(self, key):
        if self.authorize('questionary'):
            questions = self.request.get_all('question[]')

            ordinal = 0
            for question in questions:
                ordinal = ordinal + 1
                q = db.Query(Question).filter('__key__', db.Key(question)).get()
                q.ordinal = ordinal
                q.put()


class DeleteQuestionary(boRequestHandler):
    def get(self, key):
        if self.authorize('questionary'):
            for q in db.Query(Question).filter('questionary', db.Key(key)).fetch(1000):
                q.delete()

            q = db.Query(Questionary).filter('__key__', db.Key(key)).get()
            q.delete()
            self.redirect('/questionary')


class EditQuestion(boRequestHandler):
    def post(self):
        if self.authorize('questionary'):
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


class DeleteQuestion(boRequestHandler):
    def get(self, key):
        if self.authorize('questionary'):
            q = db.Query(Question).filter('__key__', db.Key(key)).get()
            q.delete()


class GenerateQuestionaryPersons(boRequestHandler):
    def get(self):
        if self.authorize('questionary'):

            self.response.headers['Content-Type'] = 'text/plain; charset=UTF-8'

            currentdate = datetime.now().date()
            #for course in db.Query(Course).filter('course_end_date <=', currentdate).filter('is_feedback_started', False).order('-course_end_date').fetch(1000):
            course = Course().get_by_key_name('course_8361')
            if course:
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
            ('/questionary/sort/(.*)', SortQuestionary),
            ('/questionary/delete/(.*)', DeleteQuestionary),
            ('/questionary/results/(.*)', ShowQuestionaryResults),
            ('/questionary/question/delete/(.*)', DeleteQuestion),
            ('/questionary/question', EditQuestion),
            ('/questionary/(.*)', ShowQuestionary),
        ])


if __name__ == '__main__':
    main()