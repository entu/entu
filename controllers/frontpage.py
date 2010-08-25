import bo
from database.person import *


class Frontpage(bo.webapp.RequestHandler):
    def get(self):
        if Person().current():
            self.redirect('/dashboard')

        bo.view(self, '', 'frontpage.html')


def main():
    bo.app([
             ('/', Frontpage),
            ])


if __name__ == '__main__':
    main()