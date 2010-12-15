from datetime import datetime

from bo import *
from database import *


class ShowFeedback(boRequestHandler):

    def get(self):
        personQuestionary = db.Query(QuestionaryPerson).filter('person', Person().current).filter('is_completed', False).order('__key__').fetch(1000)
        if len(personQuestionary) > 0:
            questions = []
            for question in personQuestionary[0].answers:
                if question.target_person:
                    target_person = question.target_person.displayname
                else:
                    target_person = ''
                questions.append({
                    'key': str(question.key()),
                    'ordinal': question.question.ordinal,
                    'question': question.question.name.translate(),
                    'answer': question.answer,
                    'type': question.question.type,
                    'target_person': target_person,
                    'is_mandatory': question.question.is_mandatory,
                })

            self.view('feedback', 'feedback_show.html', {
                'questionary': personQuestionary[0],
                'questions': questions,
                'count': len(personQuestionary)
            })
        else:
            url = Cache().get('redirect_after_feedback')
            Cache().set('redirect_after_feedback')
            if not url:
                url = '/'
            self.redirect(url)

    def post(self):
        qp = db.Query(QuestionaryPerson).filter('person', Person().current).filter('__key__', db.Key(self.request.get("person_questionary"))).get()

        if qp:
            mandatory_ok = True
            for qanswer in qp.answers:
                answer = self.request.get(str(qanswer.key())).strip()

                qanswer.question_string = qanswer.question.name.translate()
                qanswer.datetime = datetime.now()
                qanswer.answer = answer
                qanswer.put()

                if qanswer.question.is_mandatory == True:
                    if qanswer.question.type == 'like' and int(answer) == 0:
                        mandatory_ok = False
                    if qanswer.question.type == 'rating' and int(answer) < 1:
                        mandatory_ok = False
                    if qanswer.question.type == 'text' and len(answer) < 1:
                        mandatory_ok = False

            if mandatory_ok == True:
                qp.is_completed = True
                qp.put()
                self.redirect('/feedback')
            else:
                self.redirect('')


def main():
    Route([
            ('/feedback', ShowFeedback),
        ])


if __name__ == '__main__':
    main()