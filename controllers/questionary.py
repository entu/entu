import datetime

from bo import *
from database import *
from datetime import datetime

class ShowQuestionaries(webapp.RequestHandler):
    def get(self):
        q = db.Query(Questionary).fetch(1000)
        View(self, 'questionary', 'questionary_list.html', {
            'questionaries': q,
        })

    def post(self):
        name = self.request.get('name').strip()
        start_date = self.request.get('start_date').strip()
        end_date = self.request.get('end_date').strip()
        description = self.request.get('description').strip()

        q = Questionary()
        q.name = DictionaryAdd('questionary_name', name)
        if start_date:
            q.start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            q.end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        q.description = DictionaryAdd('questionary_description', description)
        q.put()

        self.redirect('')


class ShowQuestionary(webapp.RequestHandler):
    def get(self, key):
        q = db.Query(Questionary).filter('__key__', db.Key(key)).get()

        View(self, 'questionary', 'questionary.html', {
            'questionary': q,
        })

    def post(self, key):
        name = self.request.get('name').strip()
        type = self.request.get('type').strip()
        mandatory = self.request.get('mandatory').strip()
        teacher_specific = self.request.get('teacher_specific').strip()

        q = Question()
        q.questionary = db.Key(key)
        q.name = DictionaryAdd('question_name', name)
        q.type = type
        if mandatory:
            q.is_mandatory = True
        if teacher_specific:
            q.is_teacher_specific = True
        q.put()

        self.redirect('')
        
class EditQuestionary(webapp.RequestHandler):
    def get(self, key):
        q = db.Query(Questionary).filter('__key__', db.Key(key)).get()

        View(self, 'questionary', 'questionary_edit.html', {
            'questionary': q,
        })
        
    def post(self, key):
        name = self.request.get('name').strip()
        start_date = self.request.get('start_date').strip()
        end_date = self.request.get('end_date').strip()
        description = self.request.get('description').strip()
        
        q = db.get(key)
        q.name = DictionaryAdd('questionary_name', name)
        if start_date:
            q.start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            q.end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        q.description = DictionaryAdd('questionary_description', description)
        q.put()

        self.redirect('/questionary')
        
class DeleteQuestionary(webapp.RequestHandler):
    def get(self, key):
        q = db.Query(Questionary).filter('__key__', db.Key(key)).get()
        q.delete()
        self.redirect('/questionary')
        
class DeleteQuestion(webapp.RequestHandler):
    def get(self, questionary_key, question_key):
        q = db.Query(Question).filter('__key__', db.Key(question_key)).get()
        q.delete()
        self.redirect('/questionary/' + questionary_key)
        
class GenerateQuestionaryPersons(webapp.RequestHandler):
    def get(self):
        currentdate = datetime.now().date()
        courses = db.Query(Course).filter('course_end_date', currentdate)
        for course in courses:
            #db.Query(Questionary).filter('start_date <=', currentdate).filter('end_date >=', currentdate).count()
            for q in db.Query(Questionary).filter('end_date >=', currentdate):
                if q.start_date <= currentdate:             
                    qpCount = db.Query(QuestionaryPerson).filter('course', course).filter('questionary', q).count()
                    if qpCount == 0:
                        for s in course.subscribers:
                            qp = QuestionaryPerson()
                            qp.person = s.student
                            qp.is_completed = False
                            qp.questionary = q
                            qp.course = course
                            qp.put()
        
def main():
    Route([
            ('/questionary', ShowQuestionaries),
            ('/questionary/generate', GenerateQuestionaryPersons),
            ('/questionary/edit/(.*)', EditQuestionary),
            ('/questionary/delete/(.*)', DeleteQuestionary),
            ('/questionary/(.*)/delete/(.*)', DeleteQuestion),
            ('/questionary/(.*)', ShowQuestionary)
        ])


if __name__ == '__main__':
    main()