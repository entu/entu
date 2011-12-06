from bo import *
from database.zimport.zbubble import *
from database.zimport.zperson import *
from database.zimport.zbubbleperson import *


class ZimportAll(boRequestHandler):
    def get(self):
        taskqueue.Task(url='/zimport').add()

    def post(self):
        zimports = [zRatingScale, zGradeDefinition, zBubbleType, zRole, zBubble, zPerson, zBubblePerson, zContact, zGrade]
        for z in zimports:
            if db.Query(z).get():
                for e in db.Query(z).fetch(100):
                    e.zimport()
                    self.echo(str(e.key()))
                break
        for z in zimports:
            if db.Query(z).get():
                taskqueue.Task(url='/zimport').add()
                break


def main():
    Route([
            ('/zimport', ZimportAll),
        ])


if __name__ == '__main__':
    main()
