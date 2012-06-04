from bo import *


class RedirectToARX(boRequestHandler):
    def get(self, url):
        self.redirect('http://eka.arx.ee/static/error/offline.html')


def main():
    Route([
             ('/(.*)', RedirectToARX),
            ])


if __name__ == '__main__':
    main()
