from google.appengine.api import users
from datetime import date

from bo import *
from database.bubble import *
from database.person import *
from database.zimport.zbubble import *
from database.zimport.zoin import *


class Update(boRequestHandler):
    def get(self):

        self.header('Content-Type', 'text/plain; charset=utf-8')

        a = db.Query(Aggregation)
        ac = a.count(limit=2000000)

        b = db.Query(AggregationValue)
        bc = b.count(limit=2000000)

        self.echo(str(ac))
        self.echo(str(bc))


class Sort_est(boRequestHandler):
    def get(self):
        for b in db.Query(Bubble).filter('model_version', 'B').fetch(1000):
            if b.name:
                if b.name.estonian:
                    b.sort_estonian = StringToSortable(b.name.estonian)
                if b.name.english:
                    b.sort_english = StringToSortable(b.name.english)
                b.model_version = 'A'
                b.put()


class Sort_est2(boRequestHandler):
    def get(self):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        self.echo('A:' + str(db.Query(Bubble).filter('model_version', 'A').count(limit=100000)))
        self.echo('B:' + str(db.Query(Bubble).filter('model_version', 'B').count(limit=100000)))


class PersonUser(boRequestHandler):
    def get(self):
        for p in db.Query(Person).filter('model_version', 'A').fetch(1000):
            if p.apps_username and not p.user:
                p.user = users.User(p.apps_username)
            p.model_version = 'B'
            p.put()


class PersonSearchable(boRequestHandler):
    def get(self):
        for p in db.Query(Person).filter('model_version != ', 'searchable').fetch(1000):
            p.index_names()
            p.model_version = 'searchable'
            p.put()


class PersonUser2(boRequestHandler):
    def get(self):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        self.echo('A:' + str(db.Query(Person).filter('model_version', 'A').count(limit=100000)))
        self.echo('B:' + str(db.Query(Person).filter('model_version', 'B').count(limit=100000)))


class GradeI(boRequestHandler):
    def get(self):
        self.header('Content-Type', 'text/plain; charset=utf-8')

        p = []
        for g in db.Query(Grade).filter('datetime >=', date(2011, 1, 3)).filter('bubble_type', 'course').filter('is_deleted', False).fetch(1000):
            p.append(g.person.key())

        p = GetUniqueList(p)
        self.echo(str(len(p)))


class Log(boRequestHandler):
    def get(self):

        self.header('Content-Type', 'text/plain; charset=utf-8')

        bubble = Bubble().get_by_id(1622190)
        bubble.leechers.remove(db.Key('agdib25nYXBwcg4LEgZQZXJzb24YvqZuDA'))
        bubble.put()


class PRUpdate(boRequestHandler): # copy roles from PersonRole
    def get(self):

        self.header('Content-Type', 'text/plain; charset=utf-8')

        for pr in PersonRole().all():
            if not pr.person.roles:
                pr.person.roles = []
            
            pr.person.roles = AddToList(pr.role.key(), pr.person.roles)
            
            pr.person.put()




def main():
    Route([
            ('/update', Update),
            ('/update/sort', Sort_est),
            ('/update/sort2', Sort_est2),
            ('/update/user', PersonUser),
            ('/update/user2', PersonUser2),
            ('/update/grade', GradeI),
            ('/update/log3', Log),
            ('/update/prupdate', PRUpdate),
            ('/update/searchable', PersonSearchable),
        ])


if __name__ == '__main__':
    main()