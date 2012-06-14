from bo import *


class RedirectToEntu(boRequestHandler):
    def get(self, url):
        self.redirect('http://entu.artun.ee')


class RedirectToEntuPublic(boRequestHandler):
    def get(self, url):
        self.redirect('http://entu.artun.ee/public')


class RedirectToEntuApplication(boRequestHandler):
    def get(self, url):
        self.redirect('http://entu.artun.ee/application')


def main():
    Route([
        ('/application(.*)', RedirectToEntuApplication),
        ('/public(.*)', RedirectToEntuPublic),
        ('/(.*)', RedirectToEntu),
    ])


if __name__ == '__main__':
    main()
