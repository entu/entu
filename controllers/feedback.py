from bo import *
from database import *


class ShowFeedback(webapp.RequestHandler):

    def get(self):

        questionaries = db.Query(QuestionaryPerson).filter('person', Person().current()).fetch(100)

        if questionaries:



        View(self, 'feedback', 'feedback_show.html')



def main():
    Route([
            ('/feedback', ShowFeedback),
        ])


if __name__ == '__main__':
    main()