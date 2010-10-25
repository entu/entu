from bo import *
from database import *
from datetime import datetime
import cgi


class ShowFeedback(webapp.RequestHandler):

    def get(self):
        count = db.Query(QuestionaryPerson).filter('person', Person().current()).filter('is_completed', False).count()
        if count > 0:
            personQuestionary = db.Query(QuestionaryPerson).filter('person', Person().current()).filter('is_completed', False).get()
            
            View(self, 'feedback', 'feedback_show.html', {
                'personQuestionary': personQuestionary,
                'count': count
            })
        # if there are no unanswered questionaries
        #else:


    def post(self):
        qp = db.get(self.request.get("personQuestionaryId"))
        qanswers = qp.questionary_answers
        
        message = ''
        for qanswer in qanswers:
            answer = self.request.get(str(qanswer.key()))    

            if answer and len((str(answer)).strip()) > 0:
                qanswer.question_string = qanswer.question.question.translate()
                qanswer.answer = cgi.escape(answer)
                qanswer.datetime = datetime.now()
                qanswer.put()
            elif qanswer.is_mandatory and (len((str(answer)).strip()) == 0 or not answer):
                message += Translate('answer_mandatory_question') + qanswer.question.question.translate() + '<br/>'    
        
        count = db.Query(QuestionaryPerson).filter('person', Person().current()).filter('is_completed', False).count()        
        if(len(message) == 0):
                qp.is_completed = True
                qp.put()
                #self.redirect('/')
                self.get()
        else:
            View(self, 'feedback', 'feedback_show.html', {
                'personQuestionary': qp,
                'count': count,
                'errorMessage': message
                })
        
def main():
    Route([
            ('/feedback', ShowFeedback),
        ])


if __name__ == '__main__':
    main()