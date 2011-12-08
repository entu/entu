from google.appengine.api import users
from datetime import *
import time

from bo import *
from database.bubble import *
from database.person import *
from database.zimport.zoin import *
from database.zimport.zbubble import *


class ExportDocs(boRequestHandler):
    def get(self):
        taskqueue.Task(url='/update/docs').add()
        self.header('Content-Type', 'text/plain; charset=utf-8')
        self.echo(str(db.Query(Document).count(limit=1000000)))

    def post(self):
        csv = []
        for d in db.Query(Document).fetch(3000):
            users = []
            try:
                for p in Person().get(GetUniqueList([d.uploader.key()] + d.uploader.merged_to)):
                    if p.user:
                        users = MergeLists(users, p.user)
            except:
                pass

            if len(users) > 0:
                title = d.title.value if d.title else ''
                csv.append(' '.join(users) + ';' + title + ';' + str(d.file.key()))

        SendMail(
            to = 'argo.roots@artun.ee',
            subject = 'Documents',
            message = 'jee',
            attachments = [('Bubbledu_Documents.csv', '\n'.join(csv))],
        )


class ExportCv(boRequestHandler):
    def get(self):
        taskqueue.Task(url='/update/cv', params={'offset': 0}).add()
        taskqueue.Task(url='/update/cv', params={'offset': 1000}).add()
        taskqueue.Task(url='/update/cv', params={'offset': 2000}).add()
        taskqueue.Task(url='/update/cv', params={'offset': 3000}).add()
        self.header('Content-Type', 'text/plain; charset=utf-8')
        self.echo(str(db.Query(Cv).count(limit=1000000)))

    def post(self):
        csv = []
        offset = self.request.get('offset').strip()
        for d in db.Query(Cv).fetch(limit=1000, offset=int(offset)):
            users = []
            try:
                for p in Person().get(GetUniqueList([d.parent().key()] + d.parent().merged_to)):
                    if p.user:
                        users = MergeLists(users, p.user)
            except:
                pass

            if len(users) > 0:
                csv.append('"%s";"%s";"%s";"%s";"%s";"%s"' % (' '.join(users), d.type, d.organisation, d.start, d.end, d.description))

        SendMail(
            to = 'argo.roots@artun.ee',
            subject = 'CVs %s+' % offset,
            message = 'jee',
            attachments = [('Bubbledu_CVs.csv', '\n'.join(csv))],
        )


class ExportContacts(boRequestHandler):
    def get(self):
        taskqueue.Task(url='/update/contacts', params={'offset': 0}).add()
        taskqueue.Task(url='/update/contacts', params={'offset': 1000}).add()
        taskqueue.Task(url='/update/contacts', params={'offset': 2000}).add()
        taskqueue.Task(url='/update/contacts', params={'offset': 3000}).add()
        taskqueue.Task(url='/update/contacts', params={'offset': 4000}).add()
        taskqueue.Task(url='/update/contacts', params={'offset': 5000}).add()
        taskqueue.Task(url='/update/contacts', params={'offset': 6000}).add()
        self.header('Content-Type', 'text/plain; charset=utf-8')
        self.echo(str(db.Query(Contact).filter('is_deleted', False).count(limit=1000000)))

    def post(self):
        csv = []
        offset = self.request.get('offset').strip()
        for d in db.Query(Contact).filter('is_deleted', False).fetch(limit=1000, offset=int(offset)):
            users = []
            try:
                for p in Person().get(GetUniqueList([d.parent().key()] + d.parent().merged_to)):
                    if p.user:
                        users = MergeLists(users, p.user)
            except:
                pass

            if len(users) > 0:
                csv.append('"%s";"%s";"%s"' % (' '.join(users), d.type, d.value))

        SendMail(
            to = 'argo.roots@artun.ee',
            subject = 'Contacts %s+' % offset,
            message = 'jee',
            attachments = [('Bubbledu_Contacts.csv', '\n'.join(csv))],
        )


class FindStuff(boRequestHandler):
    def get(self):

        limit = 3000
        offset = self.request.get('offset', '0').strip()

        self.header('Content-Type', 'text/plain; charset=utf-8')
        for p in db.Query(Person).filter('is_guest', False):
            if not db.Query(Zoin).filter('new_entity', p).get():
                self.echo('%s %s' % (p.key(), p.displayname))
                p.delete()


class DeleteStuff(boRequestHandler):
    def get(self):
        taskqueue.Task(url='/update/delete', params={'offset': 0}).add()
        taskqueue.Task(url='/update/delete', params={'offset': 1}).add()
        taskqueue.Task(url='/update/delete', params={'offset': 2}).add()
        taskqueue.Task(url='/update/delete', params={'offset': 3}).add()
        taskqueue.Task(url='/update/delete', params={'offset': 4}).add()
        taskqueue.Task(url='/update/delete', params={'offset': 5}).add()
        taskqueue.Task(url='/update/delete', params={'offset': 6}).add()
        self.echo(str(db.Query(ChangeLog).filter('kind_name', 'Bubble').count(limit=1000000)))

    def post(self):
        limit = 10000
        offset = self.request.get('offset').strip()
        for d in db.Query(ChangeLog).filter('kind_name', 'Bubble').order('_created').fetch(limit=limit, offset=int(offset)*limit):
            if not hasattr(d, 'new_value'):
                d.delete()


def main():
    Route([
            ('/update/docs', ExportDocs),
            ('/update/cv', ExportCv),
            ('/update/contacts', ExportContacts),
            ('/update/delete', DeleteStuff),
            ('/update/find', FindStuff),
        ])


if __name__ == '__main__':
    main()
