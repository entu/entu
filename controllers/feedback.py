from bo import *
from database import *
from datetime import datetime
import cgi


class ShowFeedback(webapp.RequestHandler):

    def get(self):
        personQuestionary = db.Query(QuestionaryPerson).filter('person', Person().current()).filter('is_completed', False).order('__key__').fetch(1000)
        if len(personQuestionary) > 0:
            questions = []
            for question in personQuestionary[0].questionary_answers:
                if question.teacher:
                    teacher = question.teacher.forename + ' ' + question.teacher.surname
                else:
                    teacher = ''
                questions.append({
                    'key': str(question.key()),
                    'ordinal': question.question.ordinal,
                    'question': question.question.name.translate(),
                    'answer': question.answer,
                    'type': question.question.type,
                    'teacher': teacher,
                    'is_mandatory': question.question.is_mandatory,
                })

            View(self, 'feedback', 'feedback_show.html', {
                'questionary': personQuestionary[0],
                'questions': questions,
                'count': len(personQuestionary)
            })
        else:
            self.redirect('/')

    def post(self):
        qp = db.Query(QuestionaryPerson).filter('person', Person().current()).filter('__key__', db.Key(self.request.get("person_questionary"))).get()

        if qp:
            mandatory_ok = True
            for qanswer in qp.questionary_answers:
                answer = self.request.get(str(qanswer.key())).strip()

                qanswer.question_string = qanswer.question.name.translate()
                qanswer.datetime = datetime.now()
                qanswer.answer = answer
                qanswer.put()

                if qanswer.question.is_mandatory == True and ((qanswer.question.type != 'likert' and len(answer) < 1) or (qanswer.question.type == 'likert' and int(answer) < 1)):
                    mandatory_ok = False

            if mandatory_ok == True:
                qp.is_completed = True
                qp.put()
                self.redirect('/')
            else:
                self.redirect('')


def main():
    Route([
            ('/feedback', ShowFeedback),
        ])


if __name__ == '__main__':
    main()