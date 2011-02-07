from bo import *
from database.zimport.zapplication import *
from database.zimport.zcurriculum import *
from database.zimport.zgrade import *


class ZimportCurriculum(boRequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        for z in db.Query(zCurriculum).fetch(100):
            z.zimport()
            self.response.out.write(str(z.key().name() + '\n'))


class ZimportExam(boRequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        for z in db.Query(zExam).fetch(100):
            z.zimport()
            self.response.out.write(str(z.key().name() + '\n'))


class ZimportReception(boRequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        for z in db.Query(zReception).fetch(100):
            z.zimport()
            self.response.out.write(str(z.key().name() + '\n'))


def main():
    Route([
            ('/zimport/curriculum', ZimportCurriculum),
            ('/zimport/exam', ZimportExam),
            ('/zimport/reception', ZimportReception),
        ])


if __name__ == '__main__':
    main()