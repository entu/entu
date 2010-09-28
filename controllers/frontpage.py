from helpers import *


class Frontpage(webapp.RequestHandler):
    def get(self):
        View(self, '', 'frontpage.html')


def main():
    Route([
             ('/', Frontpage),
            ])


if __name__ == '__main__':
    main()