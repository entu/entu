from bo import *
from database.zimport.zbubble import *
from database.zimport.zperson import *
from database.zimport.zbubbleperson import *


class ZimportBubble(boRequestHandler):
    def get(self):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        for z in db.Query(zBubble).order('order').fetch(1000):
            z.zimport()
            self.echo(str(z.key()))


class ZimportBubblePerson(boRequestHandler):
    def get(self):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        for z in db.Query(zBubblePerson).fetch(1000):
            z.zimport()
            self.echo(str(z.key()))


class ZimportBubbleType(boRequestHandler):
    def get(self):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        for z in db.Query(zBubbleType).fetch(1000):
            z.zimport()
            self.echo(str(z.key()))


class ZimportContact(boRequestHandler):
    def get(self):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        for z in db.Query(zContact).fetch(1000):
            z.zimport()
            self.echo(str(z.key()))


class ZimportGrade(boRequestHandler):
    def get(self):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        for z in db.Query(zGrade).fetch(1000):
            z.zimport()
            self.echo(str(z.key()))


class ZimportGradeDefinition(boRequestHandler):
    def get(self):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        for z in db.Query(zGradeDefinition).fetch(1000):
            z.zimport()
            self.echo(str(z.key()))


class ZimportPerson(boRequestHandler):
    def get(self):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        for z in db.Query(zPerson).fetch(1000):
            z.zimport()
            self.echo(str(z.key()))


class ZimportPersonRole(boRequestHandler):
    def get(self):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        for z in db.Query(zPersonRole).fetch(1000):
            z.zimport()
            self.echo(str(z.key()))


class ZimportRatingScale(boRequestHandler):
    def get(self):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        for z in db.Query(zRatingScale).fetch(1000):
            z.zimport()
            self.echo(str(z.key()))


class ZimportRole(boRequestHandler):
    def get(self):
        self.header('Content-Type', 'text/plain; charset=utf-8')
        for z in db.Query(zRole).fetch(1000):
            z.zimport()
            self.echo(str(z.key()))


def main():
    Route([
            ('/zimport/bubble', ZimportBubble),
            ('/zimport/bubbleperson', ZimportBubblePerson),
            ('/zimport/bubbletype', ZimportBubbleType),
            ('/zimport/contact', ZimportContact),
            ('/zimport/grade', ZimportGrade),
            ('/zimport/gradedefinition', ZimportGradeDefinition),
            ('/zimport/person', ZimportPerson),
            ('/zimport/personrole', ZimportPersonRole),
            ('/zimport/ratingscale', ZimportRatingScale),
            ('/zimport/role', ZimportRole),
        ])


if __name__ == '__main__':
    main()