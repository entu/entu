from bo import *


class RedirectToEntu(boRequestHandler):
    def get(self, url):
        self.redirect('http://eka.entu.ee')


class RedirectToEntuPublic(boRequestHandler):
    def get(self, url):
        self.redirect('http://eka.entu.ee/public')


class RedirectToEntuApplication(boRequestHandler):
    def get(self, url):
        self.redirect('http://eka.entu.ee/application')


def main():
    Route([
        ('/application(.*)', RedirectToEntuApplication),
        ('/public(.*)', RedirectToEntuPublic),
        ('/(.*)', RedirectToEntu),
    ])


if __name__ == '__main__':
    main()
