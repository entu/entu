from bo import *


class RedirectToEntu(boRequestHandler):
    def get(self, url):
        self.redirect('http://entu.artun.ee')
class RedirectToEntuPublic(boRequestHandler):
    def get(self, url):
        self.redirect('http://entu.artun.ee/public')


def main():
    Route([
        ('/public(.*)', RedirectToEntuPublic),
        ('/(.*)', RedirectToEntu),
    ])


if __name__ == '__main__':
    main()
