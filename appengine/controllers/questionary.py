import datetime

from bo import *
from database.feedback import *
from datetime import datetime


class ShowQuestionariesList(boRequestHandler):
    def get(self):
        if not self.authorize('questionary'):
            return

        self.view(
            page_title = 'page_feedback',
            template_file = 'main/list.html',
            values = {
                'list_url': '/questionary',
                'content_url': '/questionary/show',
            }
        )

    def post(self):
        if not self.authorize('questionary'):
            return

        key = self.request.get('key').strip()
        if key:
            questionary = Questionary().get(key)
            self.echo_json({
                'id': questionary.key().id(),
                'key': str(questionary.key()),
                'image': None,
                'title': questionary.displayname,
                'info': questionary.displaydate,
            })
            return

        keys = None
        search = self.request.get('search').strip().lower()
        if search:
            keys = [str(k) for k in list(db.Query(Questionary, keys_only=True).order('-start_date'))]

        if  not keys:
            keys = [str(k) for k in list(db.Query(Questionary, keys_only=True).order('-start_date'))]
        self.echo_json({'keys': keys})


class ShowQuestionary(boRequestHandler):
    def get(self, questionary_id):
        if not self.authorize('questionary'):
            return

        questionary = Questionary().get_by_id(int(questionary_id))

        self.view(
            template_file = 'questionary/questionary_info.html',
            values = {
                'questionary': questionary,
            }
        )










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
        message = ','
        message += '"Aine",'
        message += '"Oppejoud",'
        message += '"Kysimus",'
        message += '"Ankeete",'
        message += '"Vastajaid",'
        message += '"Noustujaid",'
        #message += '"Osalus",'
        message += '\n'
        courses = []
        questions = db.Query(Question).filter('type', 'like').fetch(10000)
        for course in db.Query(Course).filter('is_feedback_started', True).fetch(10000):
            for question in questions:
                teachers = {}
                for a in db.Query(QuestionAnswer).filter('course', course).filter('question', question).fetch(10000):

                    if a.target_person:
                        teacher_name = a.target_person.displayname
                    else:
                        teacher_name = '...'
                    if teacher_name not in teachers:
                        teachers[teacher_name] = {
                            'totalcount': 0,
                            'count': 0,
                            'sum': 0,
                        }
                    teachers[teacher_name]['totalcount'] += 1
                    if a.answer:
                        teachers[teacher_name]['count'] += 1
                        if int(a.answer) > 0:
                            teachers[teacher_name]['sum'] += int(a.answer)

                for t_name, t_sums in teachers.iteritems():
                    message += '"' + str(course.key()) + '",'
                    message += '"' + course.subject.name.translate().replace('"','""') + '",'
                    message += '"' + t_name + '",'
                    message += '"' + question.name.translate().replace('"','""') + '",'
                    message += str(t_sums['totalcount']) + ','
                    message += str(t_sums['count']) + ','
                    if t_sums['count'] > 0:
                        message += str(float(t_sums['sum'])/float(t_sums['count'])*100.0) + ','
                    else:
                        message += '0,'
                    #if t_sums['totalcount'] > 0:
                    #    message += str(float(t_sums['count'])/float(t_sums['totalcount'])*100.0) + ','
                    #else:
                    #    message += '0,'
                message += '\n'

        #self.echo(message)

        SendMail(
            to = 'argo.roots@artun.ee',
            subject = 'Feedback',
            message = '...',
            attachments = [('feedback_rating.csv', message)]
        )


class ShowQuestionaryResults2(boRequestHandler):
    def get(self, key):
        message = ''
        message += '"Aine",'
        message += '"Vastus",'
        message += '\n'

        for a in db.Query(QuestionAnswer).filter('question', db.Key('agdib25nYXBwchALEghRdWVzdGlvbhi74kkM')).fetch(100000):

            if a.answer:
                message += '"' + a.course.subject.name.translate().replace('"','""') + '",'
                message += '"' + a.answer.strip().replace('"','""') + '",'
                message += '\n'

        #self.echo(message)

        SendMail(
            to = 'argo.roots@artun.ee',
            subject = 'Feedback',
            message = '...',
            attachments = [('feedback_text.csv', message)]
        )


class SortQuestionary(boRequestHandler):
    def post(self, key):
        if self.authorize('questionary'):
            questions = self.request.get_all('question')

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


def main():
    Route([
            ('/questionary', ShowQuestionariesList),
            (r'/questionary/show/(.*)', ShowQuestionary),
            ('/questionary/sort/(.*)', SortQuestionary),
            ('/questionary/delete/(.*)', DeleteQuestionary),
            ('/questionary/results/(.*)', ShowQuestionaryResults),
            ('/questionary/results2/(.*)', ShowQuestionaryResults2),
            ('/questionary/question/delete/(.*)', DeleteQuestion),
            ('/questionary/question', EditQuestion),
        ])


if __name__ == '__main__':
    main()
