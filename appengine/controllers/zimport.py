from bo import *
from database.zimport.zbubble import *
from database.zimport.zperson import *
from database.zimport.zbubbleperson import *


zimports = [zRatingScale, zGradeDefinition, zBubbleType, zBubble, zRole, zPerson, zBubblePerson, zGrade, zContact]


class ZimportInfo(boRequestHandler):
    def get(self):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        for z in zimports:
            c = db.Query(z).count(limit=1000000)
            self.echo('%s %5s' % (z.kind().ljust(16), c))


class ZimportAll(boRequestHandler):
    def get(self):
        taskqueue.Task(url='/zimport').add(queue_name='one-by-one')

    def post(self):
        for z in zimports:
            if db.Query(z).get():
                for e in db.Query(z).fetch(100):
                    e.zimport()
                    self.echo(str(e.key()))
                break
        for z in zimports:
            if db.Query(z).get():
                taskqueue.Task(url='/zimport').add(queue_name='one-by-one')
                break


def main():
    Route([
            ('/zimport/info', ZimportInfo),
            ('/zimport', ZimportAll),
        ])


if __name__ == '__main__':
    main()
