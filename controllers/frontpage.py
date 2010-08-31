from bo import *
from database.person import *


class Frontpage(webapp.RequestHandler):
    def get(self):
        if User().current():
            self.redirect('/dashboard')

        View(self, '', 'frontpage.html')


def main():
    Route([
             ('/', Frontpage),
            ])


if __name__ == '__main__':
    main()